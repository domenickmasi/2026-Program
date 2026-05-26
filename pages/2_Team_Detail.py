from __future__ import annotations

import plotly.express as px
import streamlit as st

from frc_scouting_app.config import DARK_THEME

st.title("Team Detail")
st.caption("Review one team's scoring profile, match history, and advanced scouting metrics.")

advanced_df = st.session_state.get("advanced_df")
raw_df = st.session_state.get("raw_df")

if advanced_df is None or raw_df is None:
    st.warning("Load data on the main page first.")
    st.stop()

required_advanced = {
    "team",
    "points_per_match",
    "latent_match_impact",
    "decision_quality",
    "reliability_under_pressure",
}

required_raw = {
    "team",
    "match",
    "auto_points",
    "teleop_points",
    "climb_points",
    "fuel_scored",
    "fuel_attempted",
}

if not required_advanced.issubset(advanced_df.columns) or not required_raw.issubset(raw_df.columns):
    st.error("The loaded dataset is missing columns needed for the team detail page.")
    st.stop()

team_options = sorted(advanced_df["team"].dropna().astype(int).unique().tolist())
team = st.selectbox("Select Team", team_options)

team_row = advanced_df[advanced_df["team"].astype(int) == team].iloc[0]
team_matches = raw_df[raw_df["team"].astype(int) == team].sort_values("match")

st.subheader(f"Team {team}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Points/Match", f"{team_row['points_per_match']:.1f}")
c2.metric("Latent Impact", f"{team_row['latent_match_impact']:.1f}")
c3.metric("Decision Quality", f"{team_row['decision_quality']:.1f}")
c4.metric("Reliability Under Pressure", f"{team_row['reliability_under_pressure']:.1f}")

if team_matches.empty:
    st.warning("No raw match entries were found for this team.")
    st.stop()

phase_df = team_matches[["match", "auto_points", "teleop_points", "climb_points"]].melt(
    id_vars=["match"],
    var_name="phase",
    value_name="points",
)

fig = px.bar(
    phase_df,
    x="match",
    y="points",
    color="phase",
    title=f"Team {team} Match-by-Match Scoring Phase Breakdown",
)
fig.update_layout(**DARK_THEME, xaxis_title="Match", yaxis_title="Points")
st.plotly_chart(fig, use_container_width=True)

line = px.line(
    team_matches,
    x="match",
    y=["fuel_scored", "fuel_attempted"],
    markers=True,
    title="Fuel Makes vs Attempts",
)
line.update_layout(**DARK_THEME, xaxis_title="Match", yaxis_title="Fuel Count")
st.plotly_chart(line, use_container_width=True)

with st.expander("View raw match entries"):
    display_columns = [
        "match",
        "alliance",
        "auto_points",
        "teleop_points",
        "fuel_scored",
        "fuel_attempted",
        "climb_points",
        "fouls",
        "breakdown",
        "defense_played",
    ]
    available_columns = [col for col in display_columns if col in team_matches.columns]

    st.dataframe(
        team_matches[available_columns],
        use_container_width=True,
        hide_index=True,
    )

st.markdown(
    """
**Advanced metric context**
- **Latent Match Impact** is a ridge-estimated impact proxy based on scoring, cycle efficiency, endgame, reliability, and defense.
- **Decision Quality** rewards efficient shots, quick but controlled cycle pace, and lower foul load.
- **Reliability Under Pressure** penalizes volatility and downtime.
"""
)