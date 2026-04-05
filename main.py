"""Pipeline entrypoint for uitnodigingsregel dropout prediction."""

from pathlib import Path

import pandas as pd
import student_signal

from uitnodigingsregel.evaluate import load_settings
from uitnodigingsregel.modeling.predict import load_models
from uitnodigingsregel.modeling.train import train_lasso, train_random_forest, train_svm


def run_pipeline(
    train_path: Path | str,
    pred_path: Path | str,
    settings: dict,
    models_dir: Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run the full dropout prediction pipeline and return ranked predictions.

    Args:
        train_path: Path to the training CSV file.
        pred_path: Path to the prediction CSV file.
        settings: Settings dictionary (from load_settings()).
        models_dir: Directory for saving/loading model files. Defaults to Path("models").

    Returns:
        Tuple of (ranked_rf, ranked_lasso, ranked_svm) DataFrames.
    """
    if models_dir is None:
        models_dir = Path("models")

    separator = settings["separator"]
    dropout_column = settings["dropout_column"]
    studentnumber_column = settings["studentnumber_column"]
    retrain_models = settings["retrain_models"]
    random_seed = settings["random_seed"]
    knn_neighbors = settings["knn_neighbors"]

    train_df = pd.read_csv(train_path, sep=separator, engine="python")
    pred_df = pd.read_csv(pred_path, sep=separator, engine="python")

    train_df = train_df.drop_duplicates()
    pred_df = pred_df.drop_duplicates()

    prepared = student_signal.prepare(
        train_df,
        pred_df,
        target_col=dropout_column,
        id_col=studentnumber_column,
        config={"imputation": {"n_neighbors": knn_neighbors}},
    )

    if retrain_models:
        print("Training models on the data...")
        rf_model = train_random_forest(
            prepared.train_df,
            random_seed,
            dropout_column,
            settings["rf_parameters"],
            model_path=models_dir / "random_forest_regressor.joblib",
        )
        lasso_model = train_lasso(
            prepared.train_df_scaled,
            random_seed,
            dropout_column,
            settings["alpha_range"],
            model_path=models_dir / "lasso_regression.joblib",
        )
        svm_model = train_svm(
            prepared.train_df_scaled,
            random_seed,
            dropout_column,
            settings["svm_parameters"],
            model_path=models_dir / "support_vector_machine.joblib",
        )
    else:
        print("retrain_models is False in config, loading pre-trained models")
        rf_model, lasso_model, svm_model = load_models(models_dir=models_dir)

    ranked_rf = student_signal.rank(rf_model, prepared, use_scaled=False)
    ranked_lasso = student_signal.rank(lasso_model, prepared, use_scaled=True)
    ranked_svm = student_signal.rank(svm_model, prepared, use_scaled=True)

    return ranked_rf, ranked_lasso, ranked_svm


def main() -> None:
    settings = load_settings()

    # Load data: user data if available, otherwise synthetic demo data
    user_train = Path(settings["user_data_dir_train"])
    user_pred = Path(settings["user_data_dir_pred"])
    if user_train.exists() and user_pred.exists():
        train_path, pred_path = user_train, user_pred
        print("User datasets found and loaded")
    else:
        train_path = Path(settings["synth_data_dir_train"])
        pred_path = Path(settings["synth_data_dir_pred"])
        print("Pre-uploaded synthetic datasets found and loaded")

    ranked_rf, ranked_lasso, ranked_svm = run_pipeline(train_path, pred_path, settings)

    # Save output
    predictions_dir = Path("models/predictions")
    predictions_dir.mkdir(parents=True, exist_ok=True)

    save_method = settings["save_method"]
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
