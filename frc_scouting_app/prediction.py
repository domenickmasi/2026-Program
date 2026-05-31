"""Alliance-level prediction logic based on processed team metrics."""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd


EMPTY_PROFILE = {
    "projected_score": 0.0,
    "impact": 0.0,
    "reliability": 0.0,
    "defense": 0.0,
    "teams_found": 0.0,
}


def _safe_column_sum(df: pd.DataFrame, column: str) -> float:
    """Return a numeric column sum, or zero when the column is unavailable."""
    if column not in df.columns:
        return 0.0

    return float(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def _safe_column_mean(df: pd.DataFrame, column: str) -> float:
    """Return a numeric column mean, or zero when the column is unavailable."""
    if column not in df.columns or df.empty:
        return 0.0

    return float(pd.to_numeric(df[column], errors="coerce").fillna(0).mean())


def _alliance_profile(team_metrics: pd.DataFrame, teams: List[int]) -> Dict[str, float]:
    """Build a simple alliance profile from processed team metrics."""
    if "team" not in team_metrics.columns:
        return EMPTY_PROFILE.copy()

    subset = team_metrics[team_metrics["team"].astype(int).isin(teams)]

    if subset.empty:
        return EMPTY_PROFILE.copy()

    adjusted = _safe_column_sum(subset, "adjusted_contribution")
    climb_bonus = 0.35 * _safe_column_sum(subset, "climb_avg")

    projected_score = float(adjusted + climb_bonus)
    impact = _safe_column_sum(subset, "latent_match_impact")
    reliability = _safe_column_mean(subset, "reliability_under_pressure")
    defense = _safe_column_sum(subset, "defense_effectiveness")

    return {
        "projected_score": projected_score,
        "impact": impact,
        "reliability": reliability,
        "defense": defense,
        "teams_found": float(len(subset)),
    }


def _alliance_strength(profile: Dict[str, float]) -> float:
    """Combine alliance signals into one directional strength estimate."""
    return float(
        profile["projected_score"]
        + 0.07 * profile["impact"]
        + 0.02 * profile["reliability"]
        + 0.03 * profile["defense"]
    )


def _prediction_reasons(red: Dict[str, float], blue: Dict[str, float]) -> List[str]:
    """Generate short explanations for the prediction page."""
    reasons = []

    if red["impact"] >= blue["impact"]:
        reasons.append(f"Red alliance has higher estimated latent impact ({red['impact']:.1f} vs {blue['impact']:.1f}).")
    else:
        reasons.append(f"Blue alliance has higher estimated latent impact ({blue['impact']:.1f} vs {red['impact']:.1f}).")

    if red["reliability"] >= blue["reliability"]:
        reasons.append(
            f"Red alliance appears more reliable under pressure ({red['reliability']:.1f} vs {blue['reliability']:.1f})."
        )
    else:
        reasons.append(
            f"Blue alliance appears more reliable under pressure ({blue['reliability']:.1f} vs {red['reliability']:.1f})."
        )

    if red["defense"] >= blue["defense"]:
        reasons.append(f"Red alliance projects stronger defensive suppression ({red['defense']:.1f} vs {blue['defense']:.1f}).")
    else:
        reasons.append(f"Blue alliance projects stronger defensive suppression ({blue['defense']:.1f} vs {red['defense']:.1f}).")

    return reasons


def predict_match(team_metrics: pd.DataFrame, red_teams: List[int], blue_teams: List[int]) -> Dict:
    """Predict a match winner from processed scouting metrics."""
    red = _alliance_profile(team_metrics, red_teams)
    blue = _alliance_profile(team_metrics, blue_teams)

    red_strength = _alliance_strength(red)
    blue_strength = _alliance_strength(blue)

    diff = red_strength - blue_strength
    red_win_prob = float(1 / (1 + np.exp(-diff / 15)))

    known_teams = set(team_metrics["team"].dropna().astype(int).tolist()) if "team" in team_metrics.columns else set()
    missing_teams = sorted(set(red_teams + blue_teams) - known_teams)

    favored = "Red" if red_win_prob >= 0.5 else "Blue"

    return {
        "red": red,
        "blue": blue,
        "red_win_probability": red_win_prob,
        "favored": favored,
        "reasons": _prediction_reasons(red, blue),
        "missing_teams": missing_teams,
        "model_note": "Early-stage model: probabilities are directional estimates, not guaranteed outcomes.",
    }