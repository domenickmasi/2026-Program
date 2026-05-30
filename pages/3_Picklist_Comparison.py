from __future__ import annotations

import streamlit as st

st.title("Picklist / Comparison")
st.caption("Rank teams by scouting metrics and compare shortlist options side by side.")

advanced_df = st.session_state.get("advanced_df")

if advanced_df is None:
    st.warning("Load data on the main page first.")
    st.stop()

ranking_metrics = [
    "latent_match_impact",
    "adjusted_contribution",
    "decision_quality",
    "reliability_under_pressure",
    "consistency_ceiling_balance",
]

available_ranking_metrics = [metric for metric in ranking_metrics if metric in advanced_df.columns]

if not available_ranking_metrics:
    st.error("No ranking metrics are available in the processed dataset.")
    st.stop()

sort_metric = st.selectbox(
    "Sort ranking by",
    available_ranking_metrics,
    help="Choose the metric used to build the picklist order.",
)

max_rows = st.slider(
    "Teams to show",
    min_value=5,
    max_value=min(75, len(advanced_df)),
    value=min(24, len(advanced_df)),
)

ranked = advanced_df.sort_values(sort_metric, ascending=False).reset_index(drop=True)
ranked.insert(0, "rank", ranked.index + 1)

picklist_columns = [
    "rank",
    "team",
    "matches",
    "points_per_match",
    "adjusted_contribution",
    "latent_match_impact",
    "decision_quality",
    "reliability_under_pressure",
    "consistency_ceiling_balance",
]

available_picklist_columns = [col for col in picklist_columns if col in ranked.columns]

st.subheader("Ranked Picklist")
st.dataframe(
    ranked[available_picklist_columns].head(max_rows),
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "Download ranked picklist CSV",
    data=ranked[available_picklist_columns].to_csv(index=False),
    file_name="ranked_picklist.csv",
    mime="text/csv",
)

teams = sorted(advanced_df["team"].dropna().astype(int).unique().tolist())
default_teams = teams[: min(3, len(teams))]

selected = st.multiselect(
    "Select teams to compare",
    teams,
    default=default_teams,
)

if selected:
    st.subheader("Side-by-side Team Comparison")

    comparison_columns = [
        "points_per_match",
        "fuel_accuracy",
        "climb_avg",
        "defense_effectiveness",
        "decision_quality",
        "latent_match_impact",
        "reliability_under_pressure",
    ]

    available_comparison_columns = [
        col for col in comparison_columns if col in advanced_df.columns
    ]

    subset = advanced_df[advanced_df["team"].astype(int).isin(selected)]

    st.dataframe(
        subset.set_index("team")[available_comparison_columns].sort_values(
            sort_metric,
            ascending=False,
        ),
        use_container_width=True,
    )
else:
    st.info("Select at least one team to compare.")