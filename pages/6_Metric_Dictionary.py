from __future__ import annotations

import pandas as pd
import streamlit as st

from frc_scouting_app.metric_dictionary import METRIC_DICTIONARY

st.title("Metric Dictionary")
st.caption("Transparent definitions for simple and advanced scouting metrics.")

metric_df = pd.DataFrame(METRIC_DICTIONARY)

search = st.text_input(
    "Search metrics",
    placeholder="Try fuel, reliability, impact, defense...",
)

if search:
    search_lower = search.lower()
    metric_df = metric_df[
        metric_df["metric"].str.lower().str.contains(search_lower)
        | metric_df["formula"].str.lower().str.contains(search_lower)
        | metric_df["meaning"].str.lower().str.contains(search_lower)
    ]

st.dataframe(
    metric_df,
    use_container_width=True,
    hide_index=True,
)

with st.expander("Modeling honesty", expanded=True):
    st.markdown(
        """
- These metrics are **estimates**, intended for scouting decision support.
- Early-event sample sizes can be noisy, especially before each team has multiple matches.
- Latent impact is ridge-regularized to reduce overfitting and extreme coefficients.
- No single metric should decide a picklist. Use rankings, match notes, robot role, and drive-team judgment together.
"""
    )