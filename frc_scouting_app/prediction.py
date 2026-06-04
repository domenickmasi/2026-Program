"""Alliance-level prediction logic based on processed team metrics.

The model uses:
- deterministic strength proxy from adjusted contribution + latent impact
- Monte Carlo score simulation to communicate uncertainty bands
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd


def _alliance_profile(team_metrics: pd.DataFrame, teams: List[int]) -> Dict[str, float]:
    subset = team_metrics[team_metrics["team"].isin(teams)]
    if subset.empty:
        return {"projected_score": 0.0, "impact": 0.0, "reliability": 0.0, "defense": 0.0}

    projected_score = float(subset["opponent_adjusted_contribution"].sum() + 0.35 * subset["climb_avg"].sum())
    impact = float(subset["latent_match_impact"].sum())
    reliability = float(subset["reliability_under_pressure"].mean())
    defense = float(subset["defense_effectiveness"].sum())
    readiness = float(subset["match_readiness_index"].mean())
    score_std = float(np.sqrt(np.maximum((subset["ppm_std"].fillna(0) ** 2).sum(), 1)))
    climb_synergy = float((subset["climb_rate"] > 0.6).sum()) * 1.4
    return {
        "projected_score": projected_score,
        "impact": impact,
        "reliability": reliability,
        "defense": defense,
        "readiness": readiness,
        "score_std": score_std,
        "climb_synergy": climb_synergy,
    }


def predict_match(team_metrics: pd.DataFrame, red_teams: List[int], blue_teams: List[int]) -> Dict:
    red = _alliance_profile(team_metrics, red_teams)
    blue = _alliance_profile(team_metrics, blue_teams)

    red_strength = (
        red["projected_score"] + 0.07 * red["impact"] + 0.02 * red["reliability"] + 0.03 * red["readiness"] + red["climb_synergy"]
    )
    blue_strength = (
        blue["projected_score"] + 0.07 * blue["impact"] + 0.02 * blue["reliability"] + 0.03 * blue["readiness"] + blue["climb_synergy"]
    )

    diff = red_strength - blue_strength
    red_win_prob = float(1 / (1 + np.exp(-diff / 15)))
    margin = float(red_strength - blue_strength)

    # Monte Carlo confidence envelope for score uncertainty communication.
    rng = np.random.default_rng(2026)
    red_draws = rng.normal(red_strength, max(red["score_std"], 3.0), size=4000)
    blue_draws = rng.normal(blue_strength, max(blue["score_std"], 3.0), size=4000)
    red_sim_win = float((red_draws > blue_draws).mean())
    red_score_ci = (float(np.percentile(red_draws, 10)), float(np.percentile(red_draws, 90)))
    blue_score_ci = (float(np.percentile(blue_draws, 10)), float(np.percentile(blue_draws, 90)))

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
        "red_win_probability_simulated": red_sim_win,
        "projected_margin": margin,
        "red_score_ci_10_90": red_score_ci,
        "blue_score_ci_10_90": blue_score_ci,
        "favored": favored,
        "reasons": reasons,
        "missing_teams": missing_teams,
        "factor_breakdown": {
            "red_strength": red_strength,
            "blue_strength": blue_strength,
            "latent_impact_delta": red["impact"] - blue["impact"],
            "reliability_delta": red["reliability"] - blue["reliability"],
            "defense_delta": red["defense"] - blue["defense"],
            "readiness_delta": red["readiness"] - blue["readiness"],
        },
        "model_note": "Early-stage model: probabilities are directional estimates, not guaranteed outcomes.",
    }
