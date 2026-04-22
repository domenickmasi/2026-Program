from __future__ import annotations

import plotly.express as px
import streamlit as st

from frc_scouting_app.config import DARK_THEME

st.title("Team Detail")

advanced_df = st.session_state.get("advanced_df")
raw_df = st.session_state.get("raw_df")
if advanced_df is None:
    st.warning("Load data on the main page first.")
    st.stop()

team = st.selectbox("Select Team", sorted(advanced_df["team"].astype(int).tolist()))
team_row = advanced_df[advanced_df["team"] == team].iloc[0]
team_matches = raw_df[raw_df["team"] == team]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Points/Match", f"{team_row['points_per_match']:.1f}")
c2.metric("Latent Impact", f"{team_row['latent_match_impact']:.1f}")
c3.metric("Decision Quality", f"{team_row['decision_quality']:.1f}")
c4.metric("Reliability Under Pressure", f"{team_row['reliability_under_pressure']:.1f}")

phase_df = team_matches[["match", "auto_points", "teleop_points", "climb_points"]].melt(id_vars=["match"], var_name="phase", value_name="points")
fig = px.bar(phase_df, x="match", y="points", color="phase", title=f"Team {team} Match-by-Match Scoring Phase Breakdown")
fig.update_layout(**DARK_THEME, xaxis_title="Match", yaxis_title="Points")
st.plotly_chart(fig, use_container_width=True)

line = px.line(team_matches.sort_values("match"), x="match", y=["fuel_scored", "fuel_attempted"], title="Fuel Makes vs Attempts")
line.update_layout(**DARK_THEME)
st.plotly_chart(line, use_container_width=True)

st.markdown(
    """
**Advanced metric context**
- **Latent Match Impact** is a ridge-estimated impact proxy based on scoring, cycle efficiency, endgame, reliability, and defense.
- **Decision Quality** rewards efficient shots, quick but controlled cycle pace, and lower foul load.
- **Reliability Under Pressure** penalizes volatility and downtime.
"""
)
