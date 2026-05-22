"""State and orchestration helpers for Streamlit pages."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd
import streamlit as st

from frc_scouting_app.demo_data import generate_demo_data
from frc_scouting_app.ingestion import ValidationReport, load_and_standardize_csv
from frc_scouting_app.processing import compute_advanced_metrics, compute_simple_metrics


ProcessedData = tuple[pd.DataFrame, ValidationReport, pd.DataFrame | None, pd.DataFrame | None]


def _build_processed_outputs(df: pd.DataFrame, report: ValidationReport) -> ProcessedData:
    """Compute shared metric tables after ingestion has completed."""
    if report.missing_required:
        return df, report, None, None

    simple = compute_simple_metrics(df)
    advanced = compute_advanced_metrics(simple)
    return df, report, simple, advanced


@st.cache_data(show_spinner=False)
def process_uploaded_data(uploaded_bytes: bytes) -> ProcessedData:
    """Load an uploaded scouting CSV and prepare app-level metric tables."""
    df, report = load_and_standardize_csv(io.BytesIO(uploaded_bytes))
    return _build_processed_outputs(df, report)


@st.cache_data(show_spinner=False)
def process_demo_data() -> ProcessedData:
    """Generate and process fallback demo data for empty app sessions."""
    df = generate_demo_data()
    report = ValidationReport([], {}, 0, 0, ["Using synthetic demo dataset."])
    return _build_processed_outputs(df, report)


def get_active_dataset(source: str, uploaded_bytes: bytes | None = None) -> ProcessedData:
    """Return either uploaded scouting data or the built-in demo dataset."""
    if source == "upload" and uploaded_bytes is not None:
        return process_uploaded_data(uploaded_bytes)

    return process_demo_data()