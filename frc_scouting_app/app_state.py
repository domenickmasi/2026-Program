"""State and orchestration helpers for Streamlit pages."""

from __future__ import annotations

import streamlit as st

from frc_scouting_app.demo_data import generate_demo_data
from frc_scouting_app.ingestion import ValidationReport, load_and_standardize_csv
from frc_scouting_app.processing import compute_advanced_metrics, compute_simple_metrics


@st.cache_data(show_spinner=False)
def process_uploaded_data(uploaded_bytes: bytes):
    import io

    df, report = load_and_standardize_csv(io.BytesIO(uploaded_bytes))
    if report.missing_required:
        return df, report, None, None
    simple = compute_simple_metrics(df)
    advanced = compute_advanced_metrics(simple, df)
    return df, report, simple, advanced


@st.cache_data(show_spinner=False)
def process_demo_data():
    df = generate_demo_data()
    simple = compute_simple_metrics(df)
    advanced = compute_advanced_metrics(simple, df)
    report = ValidationReport([], {}, 0, 0, ["Using synthetic demo dataset."])
    return df, report, simple, advanced
