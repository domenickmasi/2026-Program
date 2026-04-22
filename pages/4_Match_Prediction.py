from __future__ import annotations

import streamlit as st

from frc_scouting_app.prediction import predict_match

st.title("Match Prediction")

advanced_df = st.session_state.get("advanced_df")
if advanced_df is None:
    st.warning("Load data on the main page first.")
    st.stop()

teams = sorted(advanced_df["team"].astype(int).tolist())

red = st.multiselect("Red Alliance Teams", teams, max_selections=3)
blue = st.multiselect("Blue Alliance Teams", teams, max_selections=3)

if len(red) == 3 and len(blue) == 3:
    pred = predict_match(advanced_df, red, blue)
    if pred["missing_teams"]:
        st.warning(
            "No processed scouting history found for team(s): "
            + ", ".join(str(t) for t in pred["missing_teams"])
        )
    st.subheader("Projected Outcome")
    c1, c2, c3 = st.columns(3)
    c1.metric("Red Projected Strength", f"{pred['red']['projected_score']:.1f}")
    c2.metric("Blue Projected Strength", f"{pred['blue']['projected_score']:.1f}")
    c3.metric("Red Win Probability", f"{pred['red_win_probability']*100:.1f}%")

    st.success(f"Favored Alliance: **{pred['favored']}**")
    st.caption(pred["model_note"])

    st.markdown("### Why the model leans this way")
    for reason in pred["reasons"]:
        st.write(f"- {reason}")
else:
    st.info("Choose exactly three teams per alliance.")
