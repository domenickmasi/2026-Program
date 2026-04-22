from __future__ import annotations

import streamlit as st

st.title("Data Health / Validation")

report = st.session_state.get("validation_report")
raw_df = st.session_state.get("raw_df")
if report is None:
    st.warning("Load data on the main page first.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Missing Required Columns", len(report.missing_required))
c2.metric("Suspicious Rows", report.suspicious_rows)
c3.metric("Duplicate Rows Merged", report.duplicate_rows_merged)

if report.missing_required:
    st.error(f"Missing required fields: {', '.join(report.missing_required)}")
else:
    st.success("All required fields detected.")

if report.warnings:
    for w in report.warnings:
        st.warning(w)

st.subheader("Canonical Field Mapping")
st.json(report.mapped_columns)

st.subheader("Quick Null Audit")
st.dataframe(raw_df.isnull().sum().rename("null_count").reset_index(names="column"), use_container_width=True)
