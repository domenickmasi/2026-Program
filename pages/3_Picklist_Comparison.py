from __future__ import annotations

import streamlit as st

st.title("Picklist / Comparison")

advanced_df = st.session_state.get("advanced_df")
if advanced_df is None:
    st.warning("Load data on the main page first.")
    st.stop()

sort_metric = st.selectbox(
    "Sort ranking by",
    [
        "latent_match_impact",
        "match_readiness_index",
        "opponent_adjusted_contribution",
        "adjusted_contribution",
        "decision_quality",
        "reliability_under_pressure",
        "consistency_ceiling_balance",
    ],
)

ranked = advanced_df.sort_values(sort_metric, ascending=False).reset_index(drop=True)
ranked.insert(0, "rank", ranked.index + 1)
st.dataframe(
    ranked[
        [
            "rank",
            "team",
            "matches",
            "points_per_match",
            "adjusted_contribution",
            "opponent_adjusted_contribution",
            "latent_match_impact",
            "match_readiness_index",
            "decision_quality",
            "reliability_under_pressure",
            "consistency_ceiling_balance",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

teams = sorted(advanced_df["team"].astype(int).tolist())
selected = st.multiselect("Select teams to compare", teams, default=teams[:3])
if selected:
    st.subheader("Side-by-side Team Comparison")
    subset = advanced_df[advanced_df["team"].isin(selected)]
    st.dataframe(subset.set_index("team")[[
        "points_per_match",
        "fuel_accuracy",
        "climb_avg",
        "defense_effectiveness",
        "defense_suppression",
        "decision_quality",
        "match_readiness_index",
        "latent_match_impact",
    ]], use_container_width=True)
