from __future__ import annotations

import streamlit as st

from frc_scouting_app.prediction import predict_match

st.title("Match Prediction")
st.caption("Choose three teams per alliance to estimate a directional match outcome.")

advanced_df = st.session_state.get("advanced_df")

if advanced_df is None:
    st.warning("Load data on the main page first.")
    st.stop()

if "team" not in advanced_df.columns:
    st.error("The processed dataset is missing team numbers.")
    st.stop()

teams = sorted(advanced_df["team"].dropna().astype(int).unique().tolist())

red = st.multiselect(
    "Red Alliance Teams",
    teams,
    max_selections=3,
)

blue_options = [team for team in teams if team not in red]

blue = st.multiselect(
    "Blue Alliance Teams",
    blue_options,
    max_selections=3,
)

if len(red) == 3 and len(blue) == 3:
    pred = predict_match(advanced_df, red, blue)

    if pred["missing_teams"]:
        st.warning(
            "No processed scouting history found for team(s): "
            + ", ".join(str(t) for t in pred["missing_teams"])
        )

    st.subheader("Selected Alliances")

    c1, c2 = st.columns(2)
    c1.markdown("**Red Alliance**")
    c1.write(", ".join(str(team) for team in red))

    c2.markdown("**Blue Alliance**")
    c2.write(", ".join(str(team) for team in blue))

    st.subheader("Projected Outcome")

    red_win_probability = pred["red_win_probability"]
    blue_win_probability = 1 - red_win_probability

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Red Strength", f"{pred['red']['projected_score']:.1f}")
    c2.metric("Blue Strength", f"{pred['blue']['projected_score']:.1f}")
    c3.metric("Red Win %", f"{red_win_probability * 100:.1f}%")
    c4.metric("Blue Win %", f"{blue_win_probability * 100:.1f}%")

    if pred["favored"] == "Red":
        st.success("Favored Alliance: **Red**")
    else:
        st.info("Favored Alliance: **Blue**")

    st.caption(pred["model_note"])

    st.markdown("### Why the model leans this way")
    for reason in pred["reasons"]:
        st.write(f"- {reason}")

else:
    st.info("Choose exactly three teams per alliance.")