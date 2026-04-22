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
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Red Projected Strength", f"{pred['red']['projected_score']:.1f}")
    c2.metric("Blue Projected Strength", f"{pred['blue']['projected_score']:.1f}")
    c3.metric("Red Win Probability", f"{pred['red_win_probability']*100:.1f}%")
    c4.metric("Projected Margin (Red-Blue)", f"{pred['projected_margin']:.1f}")

    d1, d2 = st.columns(2)
    d1.metric("Red Sim Win Probability", f"{pred['red_win_probability_simulated']*100:.1f}%")
    d2.metric(
        "Score Range (10-90%)",
        f"Red {pred['red_score_ci_10_90'][0]:.1f}-{pred['red_score_ci_10_90'][1]:.1f} | "
        f"Blue {pred['blue_score_ci_10_90'][0]:.1f}-{pred['blue_score_ci_10_90'][1]:.1f}",
    )

    st.success(f"Favored Alliance: **{pred['favored']}**")
    st.caption(pred["model_note"])

    st.markdown("### Why the model leans this way")
    for reason in pred["reasons"]:
        st.write(f"- {reason}")

    st.markdown("### Factor Delta Breakdown (Red - Blue)")
    st.dataframe(
        {k: [v] for k, v in pred["factor_breakdown"].items()},
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Choose exactly three teams per alliance.")
