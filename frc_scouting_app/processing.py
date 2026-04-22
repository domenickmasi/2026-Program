"""Simple and advanced metric computation pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd

from frc_scouting_app.config import ACTION_WEIGHTS, MIN_MATCH_SAMPLE, RIDGE_ALPHA


def compute_simple_metrics(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    working["fuel_accuracy"] = np.where(
        working["fuel_attempted"] > 0,
        working["fuel_scored"] / working["fuel_attempted"],
        0.0,
    )
    working["points_contribution"] = (
        working["auto_points"]
        + working["teleop_points"]
        + working.get("climb_points", 0)
        - working.get("fouls", 0)
    )
    working["endgame_value"] = working.get("climb_points", 0)
    cycle_series = working["cycle_time"] if "cycle_time" in working.columns else pd.Series(15.0, index=working.index)
    breakdown_series = working["breakdown"] if "breakdown" in working.columns else pd.Series(False, index=working.index)
    working["cycle_efficiency"] = np.where(cycle_series > 0, 60 / cycle_series, 0)
    working["reliability_flag"] = (~breakdown_series.astype(bool)).astype(int)

    team_simple = (
        working.groupby("team", as_index=False)
        .agg(
            matches=("match", "nunique"),
            auto_avg=("auto_points", "mean"),
            teleop_avg=("teleop_points", "mean"),
            fuel_scored_avg=("fuel_scored", "mean"),
            fuel_attempted_avg=("fuel_attempted", "mean"),
            fuel_accuracy=("fuel_accuracy", "mean"),
            climb_avg=("climb_points", "mean"),
            points_per_match=("points_contribution", "mean"),
            cycle_efficiency=("cycle_efficiency", "mean"),
            reliability=("reliability_flag", "mean"),
            defense_rate=("defense_played", "mean"),
            defense_effectiveness=("defense_effectiveness", "mean"),
            fouls_avg=("fouls", "mean"),
            ppm_std=("points_contribution", "std"),
            ppm_max=("points_contribution", "max"),
        )
        .fillna(0)
    )
    return team_simple


def _ridge_closed_form(X: np.ndarray, y: np.ndarray, alpha: float) -> np.ndarray:
    n_features = X.shape[1]
    reg = alpha * np.eye(n_features)
    return np.linalg.solve(X.T @ X + reg, X.T @ y)


def compute_advanced_metrics(team_df: pd.DataFrame) -> pd.DataFrame:
    advanced = team_df.copy()

    advanced["weighted_strength"] = (
        advanced["auto_avg"] * ACTION_WEIGHTS["auto_points"]
        + advanced["teleop_avg"] * ACTION_WEIGHTS["teleop_points"]
        + advanced["fuel_scored_avg"] * ACTION_WEIGHTS["fuel_scored"]
        + advanced["fuel_accuracy"] * ACTION_WEIGHTS["fuel_accuracy"]
        + advanced["climb_avg"] * ACTION_WEIGHTS["climb_points"]
        + advanced["reliability"] * ACTION_WEIGHTS["reliability"]
        + advanced["defense_effectiveness"] * ACTION_WEIGHTS["defense_effectiveness"]
        + advanced["cycle_efficiency"] * ACTION_WEIGHTS["cycle_efficiency"]
        + advanced["fouls_avg"] * ACTION_WEIGHTS["foul_penalty"]
    )

    # Decision Quality: rewards efficient shot selection plus low foul tendency.
    advanced["decision_quality"] = (
        0.55 * advanced["fuel_accuracy"]
        + 0.25 * np.tanh(advanced["cycle_efficiency"] / 5)
        + 0.2 * (1 - np.tanh(advanced["fouls_avg"]))
    ) * 100

    # Reliability Under Pressure: blends uptime + volatility penalty.
    advanced["reliability_under_pressure"] = (
        100 * advanced["reliability"] * (1 / (1 + advanced["ppm_std"]))
    )

    # Consistency/Ceiling balance: close to 1 means strong peak without extreme volatility.
    advanced["consistency_ceiling_balance"] = np.where(
        advanced["ppm_max"] > 0,
        (advanced["points_per_match"] / advanced["ppm_max"]).clip(0, 1),
        0,
    ) * 100

    # Adjusted contribution discounts tiny sample sizes using Bayesian-style shrinkage.
    shrink = advanced["matches"] / (advanced["matches"] + MIN_MATCH_SAMPLE)
    advanced["adjusted_contribution"] = advanced["points_per_match"] * shrink

    features = advanced[
        [
            "fuel_scored_avg",
            "cycle_efficiency",
            "climb_avg",
            "reliability",
            "defense_effectiveness",
        ]
    ].to_numpy()
    y = advanced["weighted_strength"].to_numpy()
    if len(advanced) >= 2:
        beta = _ridge_closed_form(features, y, RIDGE_ALPHA)
        advanced["latent_match_impact"] = features @ beta
    else:
        advanced["latent_match_impact"] = advanced["weighted_strength"]

    return advanced.sort_values("latent_match_impact", ascending=False).reset_index(drop=True)
