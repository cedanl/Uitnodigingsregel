"""Model evaluation: precision/recall calculations, stoplight dashboard, metrics reporting."""

from importlib.resources import files
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso
from sklearn.svm import SVC


def load_settings(
    config_file: str | None = None,
    settings_type: str = "default",
) -> dict:
    """Load settings from YAML config file.

    Args:
        config_file: Path to config YAML. Defaults to package metadata config.
        settings_type: Which settings block to load ('default' or 'custom').

    Returns:
        Dictionary of settings values.
    """
    if config_file is None:
        config_file = str(files("uitnodigingsregel.metadata") / "config.yaml")
    with open(config_file, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if settings_type == "default":
        return config["default_settings"]
    if settings_type == "custom":
        return config["custom_settings"]
    raise ValueError("No settings found. Choose 'default' or 'custom'.")


def compute_dynamic_evaluation(
    model_name: str,
    data: pd.DataFrame,
    dropout_column: str = "Dropout",
) -> pd.DataFrame:
    """Compute precision and recall at every invitation threshold.

    Implements the invitation rule from Eegdeman et al. (2022): students are
    invited from highest predicted dropout probability downward, and precision/recall
    are computed cumulatively at each rank.

    Args:
        model_name: Short model identifier (e.g. 'lasso', 'rf', 'svm').
        data: DataFrame with columns: dropout_column, 'yhat2', 'yhat2_rank', 'i'.
        dropout_column: Name of the actual dropout column.

    Returns:
        DataFrame with added precision, recall, and percentage columns.
    """
    col_flag = f"{model_name}1"
    col_total = f"totalcorrect{model_name}1"
    col_precision = f"precision{model_name}"
    col_recall = f"recall{model_name}"

    data[col_flag] = np.where((data[dropout_column] == 1) & (data["yhat2_rank"] <= data["i"]), 1, 0)

    total_dropout = len(data[data[dropout_column] == 1])
    for i in range(len(data)):
        if i < 1:
            data.loc[i, col_total] = data.loc[i, col_flag]
        else:
            data.loc[i, col_total] = data.loc[i, col_flag] + data.loc[i - 1, col_total]
        data.loc[i, col_precision] = round(data.loc[i, col_total] / data.loc[i, "i"], 2)
        data.loc[i, col_recall] = round(data.loc[i, col_total] / total_dropout, 2)
        data.loc[i, "perc_uitgenodigde_studenten"] = round((data.loc[i, "i"] / len(data)) * 100, 1)

    data.drop([col_flag, col_total, "i"], axis=1, inplace=True)
    return data


def prepare_model_predictions(
    validation_data: pd.DataFrame,
    model: RandomForestRegressor | Lasso | SVC,
    model_name: str,
    dropout_column: str = "Dropout",
) -> pd.DataFrame:
    """Generate predictions, rank them, and compute dynamic evaluation.

    Args:
        validation_data: DataFrame with features and dropout column.
        model: Trained model object.
        model_name: Short model identifier ('rf', 'lasso', 'svm').
        dropout_column: Name of the target column.

    Returns:
        DataFrame with precision and recall at every invitation threshold.
    """
    X_val = validation_data.drop(dropout_column, axis=1)

    if hasattr(model, "predict_proba"):
        pred = model.predict_proba(X_val)[:, 1]
    else:
        pred = model.predict(X_val)

    data = pd.DataFrame({dropout_column: validation_data[dropout_column], "yhat2": pred})
    data = data.sort_values(by=["yhat2"], ascending=False).reset_index(drop=True)
    data["yhat2_rank"] = data["yhat2"].rank(method="dense", ascending=False)
    data["i"] = data.index + 1

    return compute_dynamic_evaluation(model_name, data, dropout_column)


def get_stoplight_evaluation(
    precision: float,
    recall: float,
) -> tuple[str, str, str]:
    """Classify model performance into stoplight categories.

    Args:
        precision: Precision percentage (0-100).
        recall: Recall percentage (0-100).

    Returns:
        Tuple of (emoji, status_label, description).
    """
    if precision >= 40 and recall >= 40:
        return "🟢", "Betrouwbaar", "Model presteert goed voor gerichte interventies"
    if precision >= 30 and recall >= 30:
        return "🟡", "Gebruik met voorzichtigheid", "Model geeft matig signaal"
    return "🔴", "Niet bruikbaar", "Model heeft verbetering nodig"


def generate_stoplight_evaluation(
    model_predictions: dict,
    invite_pct: int = 20,
    dropout_column: str = "Dropout",
    reports_dir: Path = Path("reports"),
) -> dict:
    """Generate a stoplight evaluation dashboard for all models.

    Args:
        model_predictions: Dict mapping model names to (data, model, needs_scaling) tuples.
        invite_pct: Main decision threshold percentage.
        dropout_column: Name of the target column.
        reports_dir: Directory to save report files and figures.

    Returns:
        Dict with evaluation metrics per model plus an 'Aanbeveling' key.
    """

    def _get_summary_message(
        precision: float,
        recall: float,
        pct: int,
        total_students: int,
        total_dropouts: int,
    ) -> str:
        n_invited = int(total_students * pct / 100)
        n_identified = int(total_dropouts * recall / 100)
        n_correct = int(n_invited * precision / 100)
        return (
            f"Bij {pct}% uitgenodigde studenten ({n_invited} uit {total_students} studenten):\n"
            f"- {recall:.1f}% van alle uitvallers wordt geïdentificeerd "
            f"({n_identified} van {total_dropouts} uitvallers)\n"
            f"- {precision:.1f}% van de uitgenodigde studenten valt daadwerkelijk uit "
            f"({n_correct} van {n_invited} uitgenodigde studenten)"
        )

    model_name_map = {"Random Forest": "rf", "Lasso": "lasso", "SVM": "svm"}

    eval_results_all = {}
    model_data_info = {}
    for name, (data, model, _needs_scaling) in model_predictions.items():
        try:
            short = model_name_map.get(name, name.lower())
            eval_results = prepare_model_predictions(data, model, short, dropout_column)
            eval_results_all[name] = (eval_results, short)
            model_data_info[name] = {
                "total_students": len(data),
                "total_dropouts": int(data[dropout_column].sum()),
            }
        except (ValueError, KeyError) as e:
            print(f"Warning: Prediction failed for {name}: {e}")
            eval_results_all[name] = (None, name.lower())

    # Build metrics at multiple thresholds
    thresholds = [20, 30, 40, 50]
    summary_data = []
    evaluation_metrics: dict = {}

    for name, (eval_results, short) in eval_results_all.items():
        if eval_results is None:
            continue
        model_metrics = []
        pct_col = "perc_uitgenodigde_studenten"
        for threshold in thresholds:
            closest_idx = (eval_results[pct_col] - threshold).abs().idxmin()
            precision = eval_results.loc[closest_idx, f"precision{short}"]
            recall = eval_results.loc[closest_idx, f"recall{short}"]
            model_metrics.append((threshold, precision, recall))

            if threshold == invite_pct:
                prec_pct = precision * 100
                rec_pct = recall * 100
                _stoplight, status, message = get_stoplight_evaluation(prec_pct, rec_pct)
                info = model_data_info[name]
                summary = _get_summary_message(
                    prec_pct, rec_pct, threshold, info["total_students"], info["total_dropouts"]
                )
                evaluation_metrics[name] = {
                    "precision": prec_pct,
                    "recall": rec_pct,
                    "status": status,
                    "message": message,
                    "dutch_summary": summary,
                }

        summary_data.append(
            [name, *[f"{p * 100:.1f}% / {r * 100:.1f}%" for _, p, r in model_metrics]]
        )

    # --- Create dashboard figure ---
    fig = plt.figure(figsize=(12, 8))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 2])

    ax_dashboard = fig.add_subplot(gs[0, :])
    ax_dashboard.axis("off")
    ax_summary = fig.add_subplot(gs[1, :])
    ax_summary.axis("off")

    dashboard_data = [
        [n, f"{m['precision']:.1f}%", f"{m['recall']:.1f}%", m["status"]]
        for n, m in evaluation_metrics.items()
    ]
    tbl = ax_dashboard.table(
        cellText=dashboard_data,
        colLabels=["Model", "Precisie", "Recall", "Status"],
        loc="center",
        cellLoc="center",
        colWidths=[0.3, 0.2, 0.2, 0.3],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.5)
    ax_dashboard.set_title("Model Bruikbaarheid Dashboard (20% Uitnodigingen)", pad=20, fontsize=12)

    tbl2 = ax_summary.table(
        cellText=summary_data,
        colLabels=["Model", "20% (P/R)", "30% (P/R)", "40% (P/R)", "50% (P/R)"],
        loc="center",
        cellLoc="center",
        colWidths=[0.2, 0.2, 0.2, 0.2, 0.2],
    )
    tbl2.auto_set_font_size(False)
    tbl2.set_fontsize(10)
    tbl2.scale(1, 1.5)
    ax_summary.set_title(
        "Model Prestaties bij Verschillende Uitnodigingspercentages\n(Precisie / Recall)",
        pad=20,
        fontsize=12,
    )

    ax_precision = fig.add_subplot(gs[2, 0])
    ax_recall = fig.add_subplot(gs[2, 1])

    for name, (eval_results, short) in eval_results_all.items():
        if eval_results is None:
            continue
        pcts = eval_results["perc_uitgenodigde_studenten"].values
        precs = eval_results[f"precision{short}"].values * 100
        recs = eval_results[f"recall{short}"].values * 100
        ax_precision.plot(pcts, precs, label=name)
        ax_recall.plot(pcts, recs, label=name)

    for threshold in thresholds:
        label = f"{threshold}% drempel" if threshold == thresholds[0] else None
        ax_precision.axvline(x=threshold, color="gray", linestyle="--", alpha=0.5, label=label)
        ax_recall.axvline(x=threshold, color="gray", linestyle="--", alpha=0.5, label=label)

    ax_precision.axhline(y=30, color="yellow", linestyle="--", alpha=0.5, label="Gele drempel")
    ax_recall.axhline(y=30, color="yellow", linestyle="--", alpha=0.5, label="Gele drempel")

    for ax, title, ylabel in [
        (ax_precision, "Precisie per Uitnodigingspercentage", "Precisie %"),
        (ax_recall, "Recall per Uitnodigingspercentage", "Recall %"),
    ]:
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 101)
        ax.set_xlabel("% Uitgenodigde Studenten")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend()

    plt.tight_layout()

    reports_dir = Path(reports_dir)
    figures_dir = reports_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(figures_dir / "model_usability_dashboard_plot.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Save summary table
    with open(reports_dir / "model_summary_table.txt", "w", encoding="utf-8") as f:
        f.write("Model Prestaties bij Verschillende Uitnodigingspercentages\n")
        f.write("=" * 80 + "\n\n")
        f.write("Format: Precisie% / Recall%\n\n")
        f.write(f"{'Model':<20} {'20%':<15} {'30%':<15} {'40%':<15} {'50%':<15}\n")
        f.write("-" * 80 + "\n")
        for row in summary_data:
            f.write(f"{row[0]:<20} {row[1]:<15} {row[2]:<15} {row[3]:<15} {row[4]:<15}\n")

    # Find best model
    best_model = None
    best_score = -1.0
    for name, metrics in evaluation_metrics.items():
        score = metrics["precision"] * 0.6 + metrics["recall"] * 0.4
        if score > best_score:
            best_score = score
            best_model = name

    evaluation_metrics["Aanbeveling"] = {"model": best_model}
    return evaluation_metrics


def save_model_metrics(
    train_data: pd.DataFrame,
    train_data_scaled: pd.DataFrame,
    validation_data: pd.DataFrame,
    validation_data_scaled: pd.DataFrame,
    rf_model: RandomForestRegressor,
    lasso_model: Lasso,
    svm_model: SVC,
    dropout_column: str = "Dropout",
    reports_dir: Path = Path("reports"),
) -> dict:
    """Calculate and save R², MSE, precision, and sensitivity for all models.

    Args:
        train_data: Unscaled training data (for RF).
        train_data_scaled: Scaled training data (for Lasso/SVM).
        validation_data: Unscaled validation data (for RF).
        validation_data_scaled: Scaled validation data (for Lasso/SVM).
        rf_model: Trained Random Forest model.
        lasso_model: Trained Lasso model.
        svm_model: Trained SVM model.
        dropout_column: Name of the target column.
        reports_dir: Directory to write the report file.

    Returns:
        Dict of metrics per model.
    """
    metrics: dict = {"Random Forest": {}, "Lasso": {}, "SVM": {}}

    X_train_rf = train_data.drop(dropout_column, axis=1)
    y_train_rf = train_data[dropout_column]
    X_val_rf = validation_data.drop(dropout_column, axis=1)
    y_val_rf = validation_data[dropout_column]

    X_train_scaled = train_data_scaled.drop(dropout_column, axis=1)
    y_train_scaled = train_data_scaled[dropout_column]
    X_val_scaled = validation_data_scaled.drop(dropout_column, axis=1)
    y_val_scaled = validation_data_scaled[dropout_column]

    models_config = {
        "Random Forest": (rf_model, X_train_rf, y_train_rf, X_val_rf, y_val_rf),
        "Lasso": (lasso_model, X_train_scaled, y_train_scaled, X_val_scaled, y_val_scaled),
        "SVM": (svm_model, X_train_scaled, y_train_scaled, X_val_scaled, y_val_scaled),
    }

    for name, (model, X_train, y_train, X_val, y_val) in models_config.items():
        if name == "SVM" and hasattr(model, "predict_proba"):
            y_train_pred = (model.predict_proba(X_train)[:, 1] >= 0.5).astype(int)
            y_val_pred = (model.predict_proba(X_val)[:, 1] >= 0.5).astype(int)
        else:
            y_train_pred = model.predict(X_train)
            y_val_pred = model.predict(X_val)

        mse_train = np.mean((y_train - y_train_pred) ** 2)
        r2_train = 1 - np.sum((y_train - y_train_pred) ** 2) / np.sum(
            (y_train - np.mean(y_train)) ** 2
        )
        mse_val = np.mean((y_val - y_val_pred) ** 2)
        r2_val = 1 - np.sum((y_val - y_val_pred) ** 2) / np.sum((y_val - np.mean(y_val)) ** 2)

        y_val_pred_binary = (y_val_pred >= 0.5).astype(int)
        tp = np.sum((y_val == 1) & (y_val_pred_binary == 1))
        fp = np.sum((y_val == 0) & (y_val_pred_binary == 1))
        fn = np.sum((y_val == 1) & (y_val_pred_binary == 0))
        tn = np.sum((y_val == 0) & (y_val_pred_binary == 0))

        metrics[name] = {
            "r2_train": r2_train,
            "r2_val": r2_val,
            "mse_train": mse_train,
            "mse_val": mse_val,
            "precision": tp / (tp + fp) if (tp + fp) > 0 else 0,
            "sensitivity": tp / (tp + fn) if (tp + fn) > 0 else 0,
            "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        }

    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    with open(reports_dir / "model_evaluation.txt", "w", encoding="utf-8") as f:
        f.write("Model Evaluation Metrics\n")
        f.write("=" * 80 + "\n\n")
        for model_name, m in metrics.items():
            f.write(f"{model_name} Metrics:\n")
            f.write("-" * 40 + "\n")
            f.write(f"R² (Training): {m['r2_train']:.3f}\n")
            f.write(f"R² (Validation): {m['r2_val']:.3f}\n")
            f.write(f"MSE (Training): {m['mse_train']:.3f}\n")
            f.write(f"MSE (Validation): {m['mse_val']:.3f}\n")
            f.write(f"Precision: {m['precision']:.3f}\n")
            f.write(f"Sensitivity: {m['sensitivity']:.3f}\n")
            cm = m["confusion_matrix"]
            f.write(f"\nConfusion Matrix:\nTP: {cm['tp']}  FP: {cm['fp']}\n")
            f.write(f"FN: {cm['fn']}  TN: {cm['tn']}\n")
            f.write("\n" + "=" * 80 + "\n\n")

    return metrics


def save_threshold_analysis(
    train_data: pd.DataFrame,
    train_data_scaled: pd.DataFrame,
    validation_data: pd.DataFrame,
    validation_data_scaled: pd.DataFrame,
    rf_model: RandomForestRegressor,
    lasso_model: Lasso,
    svm_model: SVC,
    dropout_column: str = "Dropout",
    reports_dir: Path = Path("reports"),
) -> dict:
    """Generate and save threshold analysis for each model.

    Args:
        train_data: Unscaled training data.
        train_data_scaled: Scaled training data.
        validation_data: Unscaled validation data.
        validation_data_scaled: Scaled validation data.
        rf_model: Trained Random Forest model.
        lasso_model: Trained Lasso model.
        svm_model: Trained SVM model.
        dropout_column: Name of the target column.
        reports_dir: Directory to write the report file.

    Returns:
        Dict of threshold DataFrames per model.
    """
    model_configs = {
        "Random Forest": (validation_data, rf_model, "rf"),
        "Lasso": (validation_data_scaled, lasso_model, "lasso"),
        "SVM": (validation_data_scaled, svm_model, "svm"),
    }

    metrics: dict = {}
    for name, (data, model, short) in model_configs.items():
        eval_results = prepare_model_predictions(data, model, short, dropout_column)
        rows = []
        for _, row in eval_results.iterrows():
            rows.append(
                {
                    "percentage": row["perc_uitgenodigde_studenten"],
                    "precision": row[f"precision{short}"],
                    "recall": row[f"recall{short}"],
                }
            )
        metrics[name] = pd.DataFrame(rows)

    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    key_pcts = [1, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100]

    with open(reports_dir / "threshold_analysis.txt", "w", encoding="utf-8") as f:
        f.write("Threshold Analysis Results\n")
        f.write("=" * 80 + "\n\n")
        for name, df in metrics.items():
            f.write(f"{name} Model:\n")
            f.write("-" * 40 + "\n")
            f.write("Percentage  Precision  Recall\n")
            f.write("-" * 40 + "\n")
            for p in key_pcts:
                closest_idx = (df["percentage"] - p).abs().idxmin()
                row = df.loc[closest_idx]
                f.write(
                    f"{row['percentage']:>9.1f}%  {row['precision']:>9.3f}  {row['recall']:>7.3f}\n"
                )
            f.write("\n" + "=" * 80 + "\n\n")

    return metrics


def extract_model_data(lines: list[str], model_name: str) -> list[dict]:
    """Extract precision/recall data from threshold analysis text file lines.

    Args:
        lines: Lines from threshold_analysis.txt.
        model_name: Model name to look for.

    Returns:
        List of dicts with 'Precisie (%)', 'Recall (%)', '% Uitgenodigd' keys.
    """
    data = []
    collecting = False
    for line in lines:
        if f"{model_name} Model:" in line:
            collecting = True
            continue
        if collecting and line.strip() and not line.startswith("-"):
            if "Percentage" in line or "Precision" in line or "Recall" in line:
                continue
            if "=" in line:
                break
            parts = line.strip().split()
            if len(parts) >= 3:
                try:
                    pct = float(parts[0].replace("%", ""))
                    precision = float(parts[1]) * 100
                    recall = float(parts[2]) * 100
                    data.append(
                        {"Precisie (%)": precision, "Recall (%)": recall, "% Uitgenodigd": pct}
                    )
                except (ValueError, IndexError):
                    continue
    return data


def sort_and_filter_data(data: list[dict]) -> pd.DataFrame:
    """Filter evaluation data to key percentages using closest-match.

    Args:
        data: List of dicts with model evaluation data.

    Returns:
        Filtered and sorted DataFrame.
    """
    df = pd.DataFrame(data)
    target_pcts = [
        2.5,
        5.0,
        10.0,
        15.0,
        20.0,
        25.0,
        30.0,
        40.0,
        50.0,
        60.0,
        70.0,
        80.0,
        90.0,
        100.0,
    ]
    selected = []
    for target in target_pcts:
        closest_idx = (df["% Uitgenodigd"] - target).abs().idxmin()
        selected.append(df.loc[closest_idx])
    return pd.DataFrame(selected).drop_duplicates().sort_values("% Uitgenodigd")


def process_evaluation_results(
    evaluation_results: dict,
    reports_dir: Path = Path("reports"),
) -> tuple:
    """Process stoplight results into display-ready format.

    Args:
        evaluation_results: Dict from generate_stoplight_evaluation.
        reports_dir: Directory containing threshold_analysis.txt.

    Returns:
        Tuple of (model_results, best_model, best_metrics,
        recommendation_display, recommendation_text).
    """
    try:
        with open(Path(reports_dir) / "threshold_analysis.txt", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    model_results = []
    for name, metrics in evaluation_results.items():
        if name == "Aanbeveling":
            continue
        if metrics["status"] == "Betrouwbaar":
            indicator = "🟢 🟢 🟢 Het model kan worden gebruikt 🟢 🟢 🟢"
        elif metrics["status"] == "Gebruik met voorzichtigheid":
            indicator = "🟡 🟡 🟡 Gebruik met voorzichtigheid 🟡 🟡 🟡"
        else:
            indicator = "🔴 🔴 🔴 Niet bruikbaar 🔴 🔴 🔴"

        model_data = (
            extract_model_data(lines, name) if name in ["Random Forest", "Lasso", "SVM"] else None
        )
        model_results.append(
            {"name": name, "indicator": indicator, "metrics": metrics, "data": model_data}
        )

    best_model = evaluation_results["Aanbeveling"]["model"]
    best_metrics = evaluation_results[best_model]

    if best_metrics["status"] == "Betrouwbaar":
        rec_display = "🟢 🟢 🟢 Het model kan worden gebruikt 🟢 🟢 🟢"
        rec_text = "Op basis van de evaluatie kan het model worden gebruikt."
    elif best_metrics["status"] == "Niet bruikbaar":
        rec_display = "🔴 🔴 🔴 Niet bruikbaar 🔴 🔴 🔴"
        rec_text = "Op basis van de evaluatie kan het model NIET worden gebruikt."
    else:
        rec_display = "🟡 Gebruik met voorzichtigheid 🟡"
        rec_text = (
            f"Op basis van de evaluatie wordt het {best_model} model "
            "aanbevolen voor gebruik met voorzichtigheid."
        )

    return model_results, best_model, best_metrics, rec_display, rec_text


def display_model_results(model_results: list[dict], model_name: str) -> str:
    """Format results for a specific model as markdown text.

    Args:
        model_results: List from process_evaluation_results.
        model_name: Name of the model to display.

    Returns:
        Formatted markdown string.
    """
    for result in model_results:
        if result["name"] != model_name:
            continue
        text = result["indicator"] + "\n"
        text += f"\n**Precisie:** {result['metrics']['precision']:.1f}%\n"
        text += f"**Recall:** {result['metrics']['recall']:.1f}%\n"
        text += f"**Status:** {result['metrics']['status']}\n"
        text += f"**Evaluatie:** {result['metrics']['message']}\n"
        text += "\n**Samenvatting:**\n"
        text += result["metrics"]["dutch_summary"] + "\n"
        text += "\n**Prestaties bij Verschillende Uitnodigingspercentages**\n"

        if result["data"] and len(result["data"]) > 0:
            df = sort_and_filter_data(result["data"]).round(1)
            text += "\n| % Uitgenodigd | Precisie (%) | Recall (%) |\n"
            text += "|:-------------:|:------------:|:----------:|\n"
            for _, row in df.iterrows():
                pct = row["% Uitgenodigd"]
                prec = row["Precisie (%)"]
                rec = row["Recall (%)"]
                text += f"| {pct:>11.1f} | {prec:>11.1f} | {rec:>10.1f} |\n"
        else:
            text += "\n*Geen gedetailleerde data beschikbaar voor dit model.*\n"
            text += "\n| % Uitgenodigd | Precisie (%) | Recall (%) |\n"
            text += "|:-------------:|:------------:|:----------:|\n"
            prec = result["metrics"]["precision"]
            rec = result["metrics"]["recall"]
            text += f"| 20.0 | {prec:>11.1f} | {rec:>10.1f} |\n"
        return text
    return ""
