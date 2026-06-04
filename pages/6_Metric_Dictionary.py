from __future__ import annotations

import pandas as pd
import streamlit as st

from frc_scouting_app.metric_dictionary import METRIC_DICTIONARY

st.title("Metric Dictionary")
st.caption("Transparent definitions for simple and advanced scouting metrics.")

st.dataframe(pd.DataFrame(METRIC_DICTIONARY), use_container_width=True, hide_index=True)

st.markdown(
    """
### Modeling honesty
- These metrics are **estimates**, intended for scouting decision support.
- Early-event sample sizes can be noisy.
- Latent impact is ridge-regularized to reduce overfitting and extreme coefficients.
"""
)
