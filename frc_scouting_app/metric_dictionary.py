"""Definitions and formulas shown in the in-app metric dictionary page."""

METRIC_DICTIONARY = [
    {
        "metric": "points_per_match",
        "formula": "mean(auto_points + teleop_points + climb_points - fouls)",
        "meaning": "Average net point contribution per observed match.",
    },
    {
        "metric": "fuel_accuracy",
        "formula": "fuel_scored / fuel_attempted",
        "meaning": "Shot conversion efficiency. A higher value means the team finishes more of its scoring attempts.",
    },
    {
        "metric": "cycle_efficiency",
        "formula": "fuel_scored / cycle_time",
        "meaning": "Approximate scoring pace. This rewards teams that score quickly without needing long cycles.",
    },
    {
        "metric": "decision_quality",
        "formula": "100 * [0.55*accuracy + 0.25*tanh(cycle_eff/5) + 0.2*(1-tanh(fouls))]",
        "meaning": "Blend of shot quality, pace, and disciplined play. Useful for separating smart scoring from volume-only scoring.",
    },
    {
        "metric": "reliability_under_pressure",
        "formula": "100 * reliability / (1 + points_std)",
        "meaning": "Rewards teams that avoid breakdowns and keep their output stable across matches.",
    },
    {
        "metric": "adjusted_contribution",
        "formula": "points_per_match * matches/(matches + k), where k=minimum sample prior",
        "meaning": "Sample-size adjusted contribution estimate. This reduces early-event overreactions from only one or two matches.",
    },
    {
        "metric": "consistency_ceiling_balance",
        "formula": "100 * (points_per_match / peak_match_points)",
        "meaning": "Shows whether a team usually performs near its best match instead of only flashing once.",
    },
    {
        "metric": "defensive_value",
        "formula": "mean(defense_effectiveness) when defense_played is true",
        "meaning": "Estimates how useful a team is when assigned to slow down opponents instead of focusing only on scoring.",
    },
    {
        "metric": "latent_match_impact",
        "formula": "ridge regression estimate from fuel_scored, cycle_efficiency, climb, reliability, defense_effectiveness",
        "meaning": "Estimated match impact beyond raw points. Treat this as a directional scouting signal, not a final ranking.",
    },
]