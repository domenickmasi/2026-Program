from __future__ import annotations

import streamlit as st

from frc_scouting_app.app_state import process_demo_data, process_uploaded_data

st.set_page_config(page_title="FRC 2026 Scouting Analytics", page_icon="🤖", layout="wide")

st.title("FRC 2026 Scouting Analytics & Match Prediction")
st.caption("Processing-first scouting stack for event strategy and early match modeling.")

with st.sidebar:
    st.header("Data Source")
    file = st.file_uploader("Upload scouting CSV", type=["csv"])
    use_demo = st.toggle("Use built-in demo data", value=file is None)

load_error = None
if file is not None and not use_demo:
    try:
        raw_df, report, simple_df, advanced_df = process_uploaded_data(file.getvalue())
    except Exception as exc:  # CSV parser and malformed input errors are surfaced in UI.
        load_error = str(exc)
        raw_df, report, simple_df, advanced_df = process_demo_data()
else:
    raw_df, report, simple_df, advanced_df = process_demo_data()

st.session_state["raw_df"] = raw_df
st.session_state["validation_report"] = report
st.session_state["simple_df"] = simple_df
st.session_state["advanced_df"] = advanced_df

if load_error:
    st.error(f"Upload failed; falling back to demo data. Details: {load_error}")

if report.missing_required:
    st.error(
        "Uploaded CSV is missing required columns: "
        + ", ".join(report.missing_required)
        + ". Please fix the source export format."
    )
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows Processed", f"{len(raw_df):,}")
c2.metric("Teams", f"{simple_df['team'].nunique():,}")
c3.metric("Matches", f"{raw_df['match'].nunique():,}")
c4.metric("Merged Duplicate Rows", report.duplicate_rows_merged)

st.info("Use pages in the left navigation to explore team analytics, picklists, predictions, and data health diagnostics.")
