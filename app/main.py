"""Streamlit app for Uitnodigingsregel dropout prediction."""

import tomllib
from pathlib import Path

import pandas as pd
import streamlit as st

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


def load_app_config() -> dict:
    """Load app-specific TOML configuration."""
    with open(Path(__file__).parent / "config.toml", "rb") as f:
        return tomllib.load(f)


app_config = load_app_config()
settings = load_settings()

st.set_page_config(page_title="Uitnodigingsregel", page_icon="🎓", layout="wide")
st.title("Uitnodigingsregel - Dropout Prediction")
st.markdown(
    "Upload trainings- en predictiedata, of gebruik de synthetische demo-data "
    "om dropout-voorspellingen te genereren."
)

# Sidebar configuration
st.sidebar.header("Instellingen")
retrain = st.sidebar.checkbox("Modellen opnieuw trainen", value=False)
save_method = st.sidebar.selectbox("Opslagformaat", ["xlsx", "csv"])

# Data loading
st.header("1. Data laden")
use_demo = st.checkbox("Gebruik synthetische demo-data", value=True)

dropout_col = app_config["settings"]["dropout_column"]
studentnr_col = app_config["settings"]["studentnumber_column"]
separator = app_config["settings"]["default_separator"]

if use_demo:
    train_path = app_config["paths"]["demo"]["train"]
    pred_path = app_config["paths"]["demo"]["pred"]
else:
    train_path = app_config["paths"]["user_data"]["train"]
    pred_path = app_config["paths"]["user_data"]["pred"]

if st.button("Data laden en pipeline uitvoeren"):
    if not Path(train_path).exists() or not Path(pred_path).exists():
        st.error(f"Databestanden niet gevonden: {train_path}, {pred_path}")
    else:
        with st.spinner("Data verwerken..."):
            train_df = pd.read_csv(train_path, sep=separator, engine="python")
            pred_df = pd.read_csv(pred_path, sep=separator, engine="python")

            train_clean = train_df.drop_duplicates()
            pred_clean = pred_df.drop_duplicates()
            train_clean, pred_clean = impute_missing_values(train_clean, pred_clean, n_neighbors=settings["knn_neighbors"])
            train_clean, pred_clean = remove_single_value_columns(train_clean, pred_clean)
            train_proc, pred_proc = convert_categorical_to_dummies(
                train_clean, pred_clean, dropout_col
            )
            train_sdd, pred_sdd = standardize_dataset(train_proc, pred_proc, dropout_col)

        if retrain:
            with st.spinner("Modellen trainen (dit kan even duren)..."):
                rf_params = settings.get("rf_parameters", {})
                alpha_range = settings.get("alpha_range", [])
                svm_params = settings.get("svm_parameters", {})
                seed = settings.get("random_seed", 42)
                rf_model = train_random_forest(train_proc, seed, dropout_col, rf_params)
                lasso_model = train_lasso(train_sdd, seed, dropout_col, alpha_range)
                svm_model = train_svm(train_sdd, seed, dropout_col, svm_params)
            st.success("Modellen getraind!")
        else:
            rf_model, lasso_model, svm_model = load_models()

        with st.spinner("Voorspellingen genereren..."):
            rf_ranked = predict_random_forest(rf_model, pred_proc, dropout_col, studentnr_col)
            lasso_ranked = predict_lasso(
                lasso_model, pred_sdd, pred_proc, dropout_col, studentnr_col
            )
            svm_ranked = predict_svm(svm_model, pred_sdd, pred_proc, dropout_col, studentnr_col)

        st.header("2. Resultaten")
        tab_rf, tab_lasso, tab_svm = st.tabs(["Random Forest", "Lasso", "SVM"])
        with tab_rf:
            st.dataframe(rf_ranked, use_container_width=True)
        with tab_lasso:
            st.dataframe(lasso_ranked, use_container_width=True)
        with tab_svm:
            st.dataframe(svm_ranked, use_container_width=True)

        st.success("Pipeline voltooid!")
