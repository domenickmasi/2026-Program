from __future__ import annotations

import streamlit as st

st.title("Data Health / Validation")
st.caption("Review CSV schema mapping, missing fields, duplicate rows, and possible scouting data issues.")

report = st.session_state.get("validation_report")
raw_df = st.session_state.get("raw_df")

if report is None or raw_df is None:
    st.warning("Load data on the main page first.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Missing Required Columns", len(report.missing_required))
c2.metric("Suspicious Rows", report.suspicious_rows)
c3.metric("Duplicate Rows Merged", report.duplicate_rows_merged)
c4.metric("Raw Entries", len(raw_df))

if report.missing_required:
    st.error(f"Missing required fields: {', '.join(report.missing_required)}")
else:
    st.success("All required fields detected.")

if report.suspicious_rows > 0:
    st.warning("Some rows may contain impossible or suspicious values. Check the warnings and raw data.")

if report.warnings:
    st.subheader("Warnings")
    for warning in report.warnings:
        st.warning(warning)
else:
    st.info("No additional validation warnings were generated.")

st.subheader("Canonical Field Mapping")

if report.mapped_columns:
    st.json(report.mapped_columns)
else:
    st.write("No mapped columns were reported.")

st.subheader("Quick Null Audit")

null_audit = (
    raw_df.isnull()
    .sum()
    .rename("null_count")
    .reset_index(names="column")
    .sort_values("null_count", ascending=False)
)

st.dataframe(
    null_audit,
    use_container_width=True,
    hide_index=True,
)

with st.expander("Preview loaded raw data"):
    st.dataframe(
        raw_df.head(50),
        use_container_width=True,
        hide_index=True,
    )