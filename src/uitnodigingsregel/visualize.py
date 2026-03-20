"""Visualization functions: precision, recall, and SVM feature importance plots."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso
from sklearn.svm import SVC

from uitnodigingsregel.evaluate import prepare_model_predictions


def save_plot(
    fig: plt.Figure,
    plot_type: str,
    figures_dir: Path = Path("reports/figures"),
) -> None:
    """Save a matplotlib figure to the reports/figures directory.

    Args:
        fig: Matplotlib figure object.
        plot_type: Identifier used in the filename.
        figures_dir: Directory to save the figure.
    """
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(figures_dir / f"{plot_type}_plot.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def generate_precision_plot(
    validation_data: pd.DataFrame,
    rf_model: RandomForestRegressor,
    lasso_model: Lasso,
    svm_model: SVC,
    validation_data_scaled: pd.DataFrame | None = None,
    dropout_column: str = "Dropout",
    do_save: bool = False,
) -> plt.Figure:
    """Generate a precision plot comparing all three models.

    Args:
        validation_data: Unscaled validation data (used for RF).
        rf_model: Trained Random Forest model.
        lasso_model: Trained Lasso model.
        svm_model: Trained SVM model.
        validation_data_scaled: Scaled validation data (for Lasso/SVM).
        dropout_column: Name of the target column.
        do_save: Whether to save the plot to file.

    Returns:
        Matplotlib Figure object.
    """
    rf_results = prepare_model_predictions(validation_data, rf_model, "rf", dropout_column)
    scaled = validation_data_scaled if validation_data_scaled is not None else validation_data
    lasso_results = prepare_model_predictions(scaled, lasso_model, "lasso", dropout_column)
    svm_results = prepare_model_predictions(scaled, svm_model, "svm", dropout_column)

    dropout_rate = (
        len(validation_data[validation_data[dropout_column] == 1]) / len(validation_data)
    ) * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        lasso_results.perc_uitgenodigde_studenten,
        lasso_results.precisionlasso * 100,
        label="lasso",
    )
    ax.plot(
        rf_results.perc_uitgenodigde_studenten,
        rf_results.precisionrf * 100,
        "-.",
        label="rf",
    )
    ax.plot(
        svm_results.perc_uitgenodigde_studenten,
        svm_results.precisionsvm * 100,
        "--",
        label="svm",
    )
    ax.axhline(y=dropout_rate, linestyle=":", label="gem")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 101)
    ax.set_xlabel("% uitgenodigde studenten")
    ax.set_ylabel("Precision %")
    ax.legend()
    ax.set_title("Precision tegen perc uitgenodigde studenten")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if do_save:
        save_plot(fig, "precision")

    return fig


def generate_sensitivity_plot(
    validation_data: pd.DataFrame,
    rf_model: RandomForestRegressor,
    lasso_model: Lasso,
    svm_model: SVC,
    validation_data_scaled: pd.DataFrame | None = None,
    dropout_column: str = "Dropout",
    do_save: bool = False,
) -> plt.Figure:
    """Generate a sensitivity (recall) plot comparing all three models.

    Args:
        validation_data: Unscaled validation data (used for RF).
        rf_model: Trained Random Forest model.
        lasso_model: Trained Lasso model.
        svm_model: Trained SVM model.
        validation_data_scaled: Scaled validation data (for Lasso/SVM).
        dropout_column: Name of the target column.
        do_save: Whether to save the plot to file.

    Returns:
        Matplotlib Figure object.
    """
    rf_results = prepare_model_predictions(validation_data, rf_model, "rf", dropout_column)
    scaled = validation_data_scaled if validation_data_scaled is not None else validation_data
    lasso_results = prepare_model_predictions(scaled, lasso_model, "lasso", dropout_column)
    svm_results = prepare_model_predictions(scaled, svm_model, "svm", dropout_column)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        lasso_results.perc_uitgenodigde_studenten,
        lasso_results.recalllasso * 100,
        label="lasso",
    )
    ax.plot(
        rf_results.perc_uitgenodigde_studenten,
        rf_results.recallrf * 100,
        "-.",
        label="rf",
    )
    ax.plot(
        svm_results.perc_uitgenodigde_studenten,
        svm_results.recallsvm * 100,
        "--",
        label="svm",
    )

    x = lasso_results.perc_uitgenodigde_studenten
    y = list(np.arange(0, 100, 100 / len(x)))
    ax.plot(x, y, ":", label="gem")

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 101)
    ax.set_xlabel("% uitgenodigde studenten")
    ax.set_ylabel("Sensitivity %")
    ax.legend()
    ax.set_title("Sensitivity tegen perc uitgenodigde studenten")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if do_save:
        save_plot(fig, "sensitivity")

    return fig


def generate_svm_importance_plot(
    validation_data: pd.DataFrame,
    svm_model: SVC,
    train_data_sdd: pd.DataFrame | None = None,
    dropout_column: str = "Dropout",
    do_save: bool = False,
) -> plt.Figure:
    """Generate feature importance plot for SVM using perturbation method.

    Args:
        validation_data: DataFrame with features and dropout column.
        svm_model: Trained SVM model.
        train_data_sdd: Scaled training data (preferred over validation_data).
        dropout_column: Name of the target column.
        do_save: Whether to save the plot to file.

    Returns:
        Matplotlib Figure object.
    """
    data = train_data_sdd.copy() if train_data_sdd is not None else validation_data.copy()
    data = data.fillna(data.mean())
    data = data.replace([np.inf, -np.inf], np.nan).fillna(data.mean())

    X = data.drop(dropout_column, axis=1)
    y = data[dropout_column]
    feature_names = X.columns

    calibrated_svm = CalibratedClassifierCV(svm_model, method="sigmoid", cv="prefit")
    calibrated_svm.fit(X, y)
    prob_original = calibrated_svm.predict_proba(X)[:, 1]

    perturbation = 1.0
    feature_stds = X.std()
    prob_changes = []
    for fname in feature_names:
        X_perturbed = X.copy()
        X_perturbed[fname] = X_perturbed[fname] + perturbation * feature_stds[fname]
        prob_perturbed = calibrated_svm.predict_proba(X_perturbed)[:, 1]
        prob_changes.append(np.mean(prob_perturbed - prob_original))

    importance_df = pd.DataFrame({"feature": feature_names, "importance": prob_changes})
    importance_df["abs_importance"] = importance_df["importance"].abs()
    importance_df = importance_df.sort_values("abs_importance", ascending=True)

    fig, ax = plt.subplots(figsize=(14, 10))
    y_pos = np.arange(len(feature_names))
    colors = ["red" if c < 0 else "green" for c in importance_df["importance"]]
    ax.barh(y_pos, importance_df["importance"], color=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(importance_df["feature"], fontsize=9)
    for i, v in enumerate(importance_df["importance"]):
        ax.text(v, i, f" {v:.4f}", va="center")

    ax.set_xlabel("Belang van Feature (Gemiddelde Verandering in Voorspelde Kans)")
    ax.set_title("SVM Feature Importance (Geschaalde Verstoring)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if do_save:
        save_plot(fig, "svm_importance")

    return fig
