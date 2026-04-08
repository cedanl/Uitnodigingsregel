"""Streamlit app for Uitnodigingsregel dropout prediction."""

import io

import pandas as pd
import streamlit as st
import student_signal

from uitnodigingsregel.evaluate import load_settings
from uitnodigingsregel.modeling.predict import load_models
from uitnodigingsregel.modeling.train import train_lasso, train_random_forest, train_svm

from styles import MAIN_CSS, START_CSS

settings = load_settings()

st.set_page_config(page_title="Uitnodigingsregel", page_icon="🎓", layout="wide")

# ─────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────

if "current_page" not in st.session_state:
    st.session_state.current_page = "start"
if "prepared" not in st.session_state:
    st.session_state.prepared = None
if "models" not in st.session_state:
    st.session_state.models = None
if "ranked" not in st.session_state:
    st.session_state.ranked = None


# ─────────────────────────────────────────────
# Start screen
# ─────────────────────────────────────────────

def show_start_screen() -> None:
    st.markdown(START_CSS, unsafe_allow_html=True)

    st.markdown("# Uitnodigingsregel")
    st.markdown(
        "Genereer dropout-voorspellingen en rangschik studenten op risico. "
        "Gebruik synthetische demo-data of upload eigen CSV-bestanden."
    )

    st.markdown("---")

    use_demo = st.checkbox("Gebruik synthetische demo-data", value=True)

    train_file = None
    pred_file = None
    if not use_demo:
        col1, col2 = st.columns(2)
        with col1:
            train_file = st.file_uploader("Trainingsdata (CSV)", type=["csv"])
        with col2:
            pred_file = st.file_uploader("Predictiedata (CSV)", type=["csv"])

    retrain = st.checkbox("Modellen opnieuw trainen", value=False)

    ready = use_demo or (train_file is not None and pred_file is not None)

    if st.button("Start analyse", type="primary", disabled=not ready):
        dropout_col = settings["dropout_column"]
        studentnr_col = settings["studentnumber_column"]
        separator = settings["separator"]

        with st.spinner("Data laden en voorbereiden..."):
            if use_demo:
                train_df = pd.read_csv(
                    settings["synth_data_dir_train"], sep=separator, engine="python"
                )
                pred_df = pd.read_csv(
                    settings["synth_data_dir_pred"], sep=separator, engine="python"
                )
            else:
                train_df = pd.read_csv(
                    io.StringIO(train_file.getvalue().decode("utf-8")),
                    sep=separator,
                    engine="python",
                )
                pred_df = pd.read_csv(
                    io.StringIO(pred_file.getvalue().decode("utf-8")),
                    sep=separator,
                    engine="python",
                )

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
        else:
            rf_model, lasso_model, svm_model = load_models()

        with st.spinner("Voorspellingen genereren..."):
            rf_ranked = student_signal.rank(rf_model, prepared, use_scaled=False)
            lasso_ranked = student_signal.rank(lasso_model, prepared, use_scaled=True)
            svm_ranked = student_signal.rank(svm_model, prepared, use_scaled=True)

        st.session_state.prepared = prepared
        st.session_state.models = {"rf": rf_model, "lasso": lasso_model, "svm": svm_model}
        st.session_state.ranked = {"rf": rf_ranked, "lasso": lasso_ranked, "svm": svm_ranked}
        st.session_state.current_page = "main"
        st.rerun()


# ─────────────────────────────────────────────
# Main screen
# ─────────────────────────────────────────────

def show_main_screen() -> None:
    st.markdown(MAIN_CSS, unsafe_allow_html=True)

    header_col, back_col = st.columns([6, 1])
    with header_col:
        st.markdown("## 🎓 Uitnodigingsregel — Resultaten")
    with back_col:
        st.markdown('<div class="nav-terug">', unsafe_allow_html=True)
        if st.button("← Terug"):
            st.session_state.current_page = "start"
            st.session_state.prepared = None
            st.session_state.models = None
            st.session_state.ranked = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    ranked = st.session_state.ranked

    tab_rf, tab_lasso, tab_svm = st.tabs(["Random Forest", "Lasso", "SVM"])

    with tab_rf:
        with st.container(border=True):
            st.markdown("**Random Forest** — rangschikking op uitvalrisico")
            st.dataframe(ranked["rf"], use_container_width=True)
            st.download_button(
                "Download RF resultaten",
                data=ranked["rf"].to_csv(index=False).encode("utf-8"),
                file_name="resultaten_rf.csv",
                mime="text/csv",
            )

    with tab_lasso:
        with st.container(border=True):
            st.markdown("**Lasso** — rangschikking op uitvalrisico")
            st.dataframe(ranked["lasso"], use_container_width=True)
            st.download_button(
                "Download Lasso resultaten",
                data=ranked["lasso"].to_csv(index=False).encode("utf-8"),
                file_name="resultaten_lasso.csv",
                mime="text/csv",
            )

    with tab_svm:
        with st.container(border=True):
            st.markdown("**SVM** — rangschikking op uitvalrisico")
            st.dataframe(ranked["svm"], use_container_width=True)
            st.download_button(
                "Download SVM resultaten",
                data=ranked["svm"].to_csv(index=False).encode("utf-8"),
                file_name="resultaten_svm.csv",
                mime="text/csv",
            )

    st.success("Pipeline voltooid!")


# ─────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────

if st.session_state.current_page == "start":
    show_start_screen()
else:
    show_main_screen()
