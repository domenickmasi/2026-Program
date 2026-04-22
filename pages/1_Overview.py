from __future__ import annotations

import plotly.express as px
import streamlit as st

from frc_scouting_app.config import DARK_THEME

st.title("Overview")

advanced_df = st.session_state.get("advanced_df")
raw_df = st.session_state.get("raw_df")
if advanced_df is None or raw_df is None:
    st.warning("Load data on the main page first.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Event Teams", int(advanced_df["team"].nunique()))
col2.metric("Avg Points/Match", f"{advanced_df['points_per_match'].mean():.1f}")
col3.metric("Avg Reliability", f"{advanced_df['reliability'].mean()*100:.1f}%")

metric = st.selectbox(
    "Top teams by metric",
    ["latent_match_impact", "adjusted_contribution", "points_per_match", "decision_quality", "reliability_under_pressure"],
)

leaderboard = advanced_df.sort_values(metric, ascending=False).head(12)
fig = px.bar(
    leaderboard,
    x="team",
    y=metric,
    color=metric,
    text=metric,
    title=f"Top Teams by {metric}",
)
fig.update_layout(**DARK_THEME, xaxis_title="Team", yaxis_title=metric)
fig.update_traces(texttemplate="%{text:.2f}")
st.plotly_chart(fig, use_container_width=True)

phase = raw_df.groupby("team", as_index=False)[["auto_points", "teleop_points", "climb_points"]].mean()
fig2 = px.scatter(
    phase,
    x="auto_points",
    y="teleop_points",
    size="climb_points",
    hover_data=["team"],
    title="Scoring Profile: Auto vs Teleop with Climb Bubble Size",
)
fig2.update_layout(**DARK_THEME)
st.plotly_chart(fig2, use_container_width=True)
