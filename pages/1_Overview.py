from __future__ import annotations

import plotly.express as px
import streamlit as st

from frc_scouting_app.config import DARK_THEME

st.title("Overview")
st.caption("Quick event summary, team leaderboard, and scoring profile visualization.")

advanced_df = st.session_state.get("advanced_df")
raw_df = st.session_state.get("raw_df")

if advanced_df is None or raw_df is None:
    st.warning("Load data on the main page first.")
    st.stop()

required_advanced = {"team", "points_per_match", "reliability"}
required_raw = {"team", "auto_points", "teleop_points", "climb_points"}

if not required_advanced.issubset(advanced_df.columns) or not required_raw.issubset(raw_df.columns):
    st.error("The loaded dataset is missing columns needed for the overview page.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Event Teams", int(advanced_df["team"].nunique()))
col2.metric("Raw Entries", int(len(raw_df)))
col3.metric("Avg Points/Match", f"{advanced_df['points_per_match'].mean():.1f}")
col4.metric("Avg Reliability", f"{advanced_df['reliability'].mean() * 100:.1f}%")

metric_options = [
    "latent_match_impact",
    "adjusted_contribution",
    "points_per_match",
    "decision_quality",
    "reliability_under_pressure",
]

available_metrics = [metric for metric in metric_options if metric in advanced_df.columns]

metric = st.selectbox(
    "Top teams by metric",
    available_metrics,
    help="Choose which advanced metric should be used to rank teams on the leaderboard.",
)

leaderboard = advanced_df.sort_values(metric, ascending=False).head(12)

fig = px.bar(
    leaderboard,
    x="team",
    y=metric,
    color=metric,
    text=metric,
    title=f"Top Teams by {metric.replace('_', ' ').title()}",
)
fig.update_layout(**DARK_THEME, xaxis_title="Team", yaxis_title=metric.replace("_", " ").title())
fig.update_traces(texttemplate="%{text:.2f}")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Scoring Profile")

phase = raw_df.groupby("team", as_index=False)[["auto_points", "teleop_points", "climb_points"]].mean()

fig2 = px.scatter(
    phase,
    x="auto_points",
    y="teleop_points",
    size="climb_points",
    hover_data=["team"],
    title="Average Auto vs Teleop Scoring",
)
fig2.update_layout(
    **DARK_THEME,
    xaxis_title="Average Auto Points",
    yaxis_title="Average Teleop Points",
)
st.plotly_chart(fig2, use_container_width=True)

with st.expander("Preview processed team metrics"):
    preview_columns = ["team", "points_per_match", "reliability"]
    if metric not in preview_columns:
        preview_columns.append(metric)

    st.dataframe(
        advanced_df[preview_columns].sort_values(metric, ascending=False).head(20),
        use_container_width=True,
        hide_index=True,
    )