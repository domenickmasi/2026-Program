"""Simple and advanced metric computation pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd

from frc_scouting_app.config import ACTION_WEIGHTS, MIN_MATCH_SAMPLE, RIDGE_ALPHA


def _numeric_series(df: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    """Return a numeric column or a default-valued series when missing."""
    if column not in df.columns:
        return pd.Series(default, index=df.index)

    return pd.to_numeric(df[column], errors="coerce").fillna(default)


def _boolean_series(df: pd.DataFrame, column: str, default: bool = False) -> pd.Series:
    """Return a boolean column or a default-valued series when missing."""
    if column not in df.columns:
        return pd.Series(default, index=df.index)

    return df[column].fillna(default).astype(bool)


def compute_simple_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-team averages and basic scouting metrics."""
    working = df.copy()

    working["auto_points"] = _numeric_series(working, "auto_points")
    working["teleop_points"] = _numeric_series(working, "teleop_points")
    working["fuel_scored"] = _numeric_series(working, "fuel_scored")
    working["fuel_attempted"] = _numeric_series(working, "fuel_attempted")
    working["climb_points"] = _numeric_series(working, "climb_points")
    working["fouls"] = _numeric_series(working, "fouls")
    working["cycle_time"] = _numeric_series(working, "cycle_time", 15.0)
    working["defense_effectiveness"] = _numeric_series(working, "defense_effectiveness")

    working["breakdown"] = _boolean_series(working, "breakdown")
    working["defense_played"] = _boolean_series(working, "defense_played")

    working["fuel_accuracy"] = np.where(
        working["fuel_attempted"] > 0,
        working["fuel_scored"] / working["fuel_attempted"],
        0.0,
    )

    working["points_contribution"] = (
        working["auto_points"]
        + working["teleop_points"]
        + working["climb_points"]
        - working["fouls"]
    )

    working["endgame_value"] = working["climb_points"]
    working["cycle_efficiency"] = np.where(working["cycle_time"] > 0, 60 / working["cycle_time"], 0)
    working["reliability_flag"] = (~working["breakdown"]).astype(int)

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
    """Solve a small ridge regression problem for the latent impact score."""
    n_features = X.shape[1]
    reg = alpha * np.eye(n_features)
    return np.linalg.solve(X.T @ X + reg, X.T @ y)


def _safe_ridge_impact(features: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Return ridge predictions, falling back to raw weights if solving fails."""
    if len(y) < 2:
        return y

    try:
        beta = _ridge_closed_form(features, y, RIDGE_ALPHA)
        return features @ beta
    except np.linalg.LinAlgError:
        return y


def compute_advanced_metrics(team_df: pd.DataFrame) -> pd.DataFrame:
    """Compute weighted, adjusted, and model-based team metrics."""
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

    advanced["decision_quality"] = (
        0.55 * advanced["fuel_accuracy"]
        + 0.25 * np.tanh(advanced["cycle_efficiency"] / 5)
        + 0.2 * (1 - np.tanh(advanced["fouls_avg"]))
    ) * 100

    advanced["reliability_under_pressure"] = (
        100 * advanced["reliability"] * (1 / (1 + advanced["ppm_std"]))
    )

    advanced["consistency_ceiling_balance"] = np.where(
        advanced["ppm_max"] > 0,
        (advanced["points_per_match"] / advanced["ppm_max"]).clip(0, 1),
        0,
    ) * 100

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
    advanced["latent_match_impact"] = _safe_ridge_impact(features, y)

    return advanced.sort_values("latent_match_impact", ascending=False).reset_index(drop=True)