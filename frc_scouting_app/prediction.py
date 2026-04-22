"""Alliance-level prediction logic based on processed team metrics."""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd


def _alliance_profile(team_metrics: pd.DataFrame, teams: List[int]) -> Dict[str, float]:
    subset = team_metrics[team_metrics["team"].isin(teams)]
    if subset.empty:
        return {"projected_score": 0.0, "impact": 0.0, "reliability": 0.0, "defense": 0.0}

    projected_score = float(subset["adjusted_contribution"].sum() + 0.35 * subset["climb_avg"].sum())
    impact = float(subset["latent_match_impact"].sum())
    reliability = float(subset["reliability_under_pressure"].mean())
    defense = float(subset["defense_effectiveness"].sum())
    return {
        "projected_score": projected_score,
        "impact": impact,
        "reliability": reliability,
        "defense": defense,
    }


def predict_match(team_metrics: pd.DataFrame, red_teams: List[int], blue_teams: List[int]) -> Dict:
    red = _alliance_profile(team_metrics, red_teams)
    blue = _alliance_profile(team_metrics, blue_teams)

    red_strength = red["projected_score"] + 0.07 * red["impact"] + 0.02 * red["reliability"]
    blue_strength = blue["projected_score"] + 0.07 * blue["impact"] + 0.02 * blue["reliability"]

    diff = red_strength - blue_strength
    red_win_prob = float(1 / (1 + np.exp(-diff / 15)))

    reasons = []
    if red["impact"] > blue["impact"]:
        reasons.append(f"Red alliance has higher estimated latent impact ({red['impact']:.1f} vs {blue['impact']:.1f}).")
    else:
        reasons.append(f"Blue alliance has higher estimated latent impact ({blue['impact']:.1f} vs {red['impact']:.1f}).")

    if red["reliability"] > blue["reliability"]:
        reasons.append(
            f"Red alliance appears more reliable under pressure ({red['reliability']:.1f} vs {blue['reliability']:.1f})."
        )
    else:
        reasons.append(
            f"Blue alliance appears more reliable under pressure ({blue['reliability']:.1f} vs {red['reliability']:.1f})."
        )

    if red["defense"] > blue["defense"]:
        reasons.append(f"Red alliance projects stronger defensive suppression ({red['defense']:.1f} vs {blue['defense']:.1f}).")
    else:
        reasons.append(f"Blue alliance projects stronger defensive suppression ({blue['defense']:.1f} vs {red['defense']:.1f}).")

    favored = "Red" if red_win_prob >= 0.5 else "Blue"
    missing_teams = sorted(
        set(red_teams + blue_teams) - set(team_metrics["team"].astype(int).tolist())
    )
    return {
        "red": red,
        "blue": blue,
        "red_win_probability": red_win_prob,
        "favored": favored,
        "reasons": reasons,
        "missing_teams": missing_teams,
        "model_note": "Early-stage model: probabilities are directional estimates, not guaranteed outcomes.",
    }
