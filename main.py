"""Pipeline entrypoint for uitnodigingsregel dropout prediction."""

from pathlib import Path

import pandas as pd

from uitnodigingsregel.dataset import impute_missing_values, remove_single_value_columns
from uitnodigingsregel.evaluate import load_settings
from uitnodigingsregel.features import convert_categorical_to_dummies, standardize_dataset
from uitnodigingsregel.modeling.predict import (
    load_models,
    predict_lasso,
    predict_random_forest,
    predict_svm,
)
from uitnodigingsregel.modeling.train import train_lasso, train_random_forest, train_svm


def main() -> None:
    settings = load_settings()

    separator = settings["separator"]
    dropout_column = settings["dropout_column"]
    studentnumber_column = settings["studentnumber_column"]
    save_method = settings["save_method"]
    retrain_models = settings["retrain_models"]
    random_seed = settings["random_seed"]
    knn_neighbors = settings["knn_neighbors"]

    # Load data: user data if available, otherwise synthetic demo data
    user_train = Path(settings["user_data_dir_train"])
    user_pred = Path(settings["user_data_dir_pred"])
    if user_train.exists() and user_pred.exists():
        train_df = pd.read_csv(user_train, sep=separator, engine="python")
        pred_df = pd.read_csv(user_pred, sep=separator, engine="python")
        print("User datasets found and loaded")
    else:
        train_df = pd.read_csv(settings["synth_data_dir_train"], sep=separator, engine="python")
        pred_df = pd.read_csv(settings["synth_data_dir_pred"], sep=separator, engine="python")
        print("Pre-uploaded synthetic datasets found and loaded")

    # Data cleaning
    train_clean = train_df.drop_duplicates()
    pred_clean = pred_df.drop_duplicates()
    train_clean, pred_clean = impute_missing_values(train_clean, pred_clean, n_neighbors=knn_neighbors)
    train_clean, pred_clean = remove_single_value_columns(train_clean, pred_clean)

    # Feature engineering
    train_processed, pred_processed = convert_categorical_to_dummies(
        train_clean, pred_clean, dropout_column
    )
    train_sdd, pred_sdd = standardize_dataset(train_processed, pred_processed, dropout_column)

    # Train or load models
    if retrain_models:
        print("Training models on the data...")
        rf_model = train_random_forest(
            train_processed, random_seed, dropout_column, settings["rf_parameters"]
        )
        lasso_model = train_lasso(train_sdd, random_seed, dropout_column, settings["alpha_range"])
        svm_model = train_svm(train_sdd, random_seed, dropout_column, settings["svm_parameters"])
    else:
        print("retrain_models is False in config, loading pre-trained models")
        rf_model, lasso_model, svm_model = load_models()

    # Predict
    ranked_rf = predict_random_forest(
        rf_model, pred_processed, dropout_column, studentnumber_column
    )
    ranked_lasso = predict_lasso(
        lasso_model, pred_sdd, pred_processed, dropout_column, studentnumber_column
    )
    ranked_svm = predict_svm(
        svm_model, pred_sdd, pred_processed, dropout_column, studentnumber_column
    )

    # Save output
    predictions_dir = Path("models/predictions")
    predictions_dir.mkdir(parents=True, exist_ok=True)

    if save_method == "xlsx":
        with pd.ExcelWriter(
            predictions_dir / "ranked_students.xlsx", engine="xlsxwriter"
        ) as writer:
            ranked_rf.to_excel(writer, sheet_name="Random Forest", index=False)
            ranked_lasso.to_excel(writer, sheet_name="Lasso", index=False)
            ranked_svm.to_excel(writer, sheet_name="Support Vector Machine", index=False)
        print("Output file saved as .xlsx in the /models/predictions folder")
    elif save_method == "csv":
        csv_dir = predictions_dir / "csv_output"
        csv_dir.mkdir(parents=True, exist_ok=True)
        ranked_rf.to_csv(csv_dir / "ranked_students_rf.csv", sep=";", index=False)
        ranked_lasso.to_csv(csv_dir / "ranked_students_lasso.csv", sep=";", index=False)
        ranked_svm.to_csv(csv_dir / "ranked_students_svm.csv", sep=";", index=False)
        print("Output files saved as .csv in the /models/predictions/csv_output folder")
    else:
        print('Invalid save method. Choose "xlsx" or "csv" in config.')


if __name__ == "__main__":
    main()
