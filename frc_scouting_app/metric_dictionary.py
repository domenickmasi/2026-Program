"""Definitions and formulas shown in the in-app metric dictionary page."""

METRIC_DICTIONARY = [
    {
        "metric": "points_per_match",
        "formula": "mean(auto_points + teleop_points + climb_points - fouls)",
        "meaning": "Average net points contribution per observed match.",
    },
    {
        "metric": "fuel_accuracy",
        "formula": "fuel_scored / fuel_attempted",
        "meaning": "Shot conversion efficiency; higher means better decision quality in scoring attempts.",
    },
    {
        "metric": "decision_quality",
        "formula": "100 * [0.55*accuracy + 0.25*tanh(cycle_eff/5) + 0.2*(1-tanh(fouls))]",
        "meaning": "Interpretable blend of shot quality, pace, and disciplined play.",
    },
    {
        "metric": "reliability_under_pressure",
        "formula": "100 * reliability / (1 + points_std)",
        "meaning": "Rewards teams that avoid breakdowns and maintain stable output under stress.",
    },
    {
        "metric": "adjusted_contribution",
        "formula": "points_per_match * matches/(matches + k), where k=minimum sample prior",
        "meaning": "Sample-size adjusted contribution estimate to reduce early-event volatility.",
    },
    {
        "metric": "consistency_ceiling_balance",
        "formula": "100 * (points_per_match / peak_match_points)",
        "meaning": "Measures whether a team regularly approaches its peak scoring ceiling.",
    },
    {
        "metric": "latent_match_impact",
        "formula": "ridge regression estimate from fuel_scored, cycle_efficiency, climb, reliability, defense_effectiveness",
        "meaning": "Estimated true match impact signal beyond raw points; use as directional scouting input.",
    },
    {
        "metric": "defense_suppression",
        "formula": "event_avg_opponent_points - avg_opponent_points_when_team_played_defense",
        "meaning": "Directional estimate of whether a team's defense coincides with reduced opponent output.",
    },
    {
        "metric": "opponent_adjusted_contribution",
        "formula": "adjusted_contribution + 0.35*defense_suppression",
        "meaning": "Two-way contribution estimate blending scoring with observed defensive suppression.",
    },
    {
        "metric": "match_readiness_index",
        "formula": "weighted blend of decision quality, reliability under pressure, consistency/ceiling, and value-over-replacement",
        "meaning": "Composite match-readiness signal for near-term strategic lineup decisions.",
    },
]
