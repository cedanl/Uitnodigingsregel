"""Streamlit app for Uitnodigingsregel dropout prediction."""

from pathlib import Path

import pandas as pd
import streamlit as st
import student_signal

from uitnodigingsregel.evaluate import load_settings
from uitnodigingsregel.modeling.predict import load_models
from uitnodigingsregel.modeling.train import train_lasso, train_random_forest, train_svm


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

dropout_col = settings["dropout_column"]
studentnr_col = settings["studentnumber_column"]
separator = settings["separator"]

if use_demo:
    train_path = settings["synth_data_dir_train"]
    pred_path = settings["synth_data_dir_pred"]
else:
    train_path = settings["user_data_dir_train"]
    pred_path = settings["user_data_dir_pred"]

if st.button("Data laden en pipeline uitvoeren"):
    if not Path(train_path).exists() or not Path(pred_path).exists():
        st.error(f"Databestanden niet gevonden: {train_path}, {pred_path}")
    else:
        with st.spinner("Data verwerken..."):
            train_df = pd.read_csv(train_path, sep=separator, engine="python")
            pred_df = pd.read_csv(pred_path, sep=separator, engine="python")

            prepared = student_signal.prepare(
                train_df.drop_duplicates(),
                pred_df.drop_duplicates(),
                target_col=dropout_col,
                id_col=studentnr_col,
                config={"imputation": {"n_neighbors": settings["knn_neighbors"]}},
            )

        if retrain:
            with st.spinner("Modellen trainen (dit kan even duren)..."):
                seed = settings.get("random_seed", 42)
                rf_model = train_random_forest(
                    prepared.train_df, seed, dropout_col, settings.get("rf_parameters", {})
                )
                lasso_model = train_lasso(
                    prepared.train_df_scaled, seed, dropout_col, settings.get("alpha_range", [])
                )
                svm_model = train_svm(
                    prepared.train_df_scaled, seed, dropout_col, settings.get("svm_parameters", {})
                )
            st.success("Modellen getraind!")
        else:
            rf_model, lasso_model, svm_model = load_models()

        with st.spinner("Voorspellingen genereren..."):
            rf_ranked = student_signal.rank(rf_model, prepared, use_scaled=False)
            lasso_ranked = student_signal.rank(lasso_model, prepared, use_scaled=True)
            svm_ranked = student_signal.rank(svm_model, prepared, use_scaled=True)

        st.header("2. Resultaten")
        tab_rf, tab_lasso, tab_svm = st.tabs(["Random Forest", "Lasso", "SVM"])
        with tab_rf:
            st.dataframe(rf_ranked, use_container_width=True)
        with tab_lasso:
            st.dataframe(lasso_ranked, use_container_width=True)
        with tab_svm:
            st.dataframe(svm_ranked, use_container_width=True)

        st.success("Pipeline voltooid!")
