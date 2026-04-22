"""Simple and advanced metric computation pipeline.

This module intentionally separates:
- row-level -> team-level simple aggregation
- team-level -> advanced interpretable derived metrics

Advanced metrics are estimation-oriented and include uncertainty/small-sample
controls so early-event data does not dominate rankings.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from frc_scouting_app.config import ACTION_WEIGHTS, MIN_MATCH_SAMPLE, RIDGE_ALPHA


def compute_simple_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute transparent first-layer team metrics from cleaned scouting rows."""
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
    working["auto_share"] = np.where(
        working["points_contribution"] > 0,
        working["auto_points"] / working["points_contribution"],
        0.0,
    )
    working["teleop_share"] = np.where(
        working["points_contribution"] > 0,
        working["teleop_points"] / working["points_contribution"],
        0.0,
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
            ppm_min=("points_contribution", "min"),
            ppm_median=("points_contribution", "median"),
            ppm_p90=("points_contribution", lambda s: np.percentile(s, 90)),
            ppm_p10=("points_contribution", lambda s: np.percentile(s, 10)),
            climb_rate=("climb_points", lambda s: float((s > 0).mean())),
            auto_share=("auto_share", "mean"),
            teleop_share=("teleop_share", "mean"),
        )
        .fillna(0)
    )
    team_simple["accuracy_volume_index"] = (
        team_simple["fuel_accuracy"] * np.sqrt(team_simple["fuel_attempted_avg"].clip(lower=0))
    )
    team_simple["consistency_band"] = team_simple["ppm_p90"] - team_simple["ppm_p10"]
    return team_simple


def _ridge_closed_form(X: np.ndarray, y: np.ndarray, alpha: float) -> np.ndarray:
    n_features = X.shape[1]
    reg = alpha * np.eye(n_features)
    return np.linalg.solve(X.T @ X + reg, X.T @ y)


def _defense_suppression_from_matches(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Estimate opponent suppression from match/alliance rows.

    If a team reports defense in a match, compare opponent alliance net score
    to event average opponent score to estimate directional suppression.
    """
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=["team", "defense_suppression"])

    df = raw_df.copy()
    df["net_points"] = df["auto_points"] + df["teleop_points"] + df.get("climb_points", 0) - df.get("fouls", 0)
    alliance_scores = df.groupby(["match", "alliance"], as_index=False).agg(
        alliance_points=("net_points", "sum")
    )
    opp = alliance_scores.copy()
    opp["alliance"] = opp["alliance"].map({"red": "blue", "blue": "red"}).fillna(opp["alliance"])
    opp = opp.rename(columns={"alliance_points": "opponent_points"})
    joined = alliance_scores.merge(opp, on=["match", "alliance"], how="left")
    league_opp_avg = joined["opponent_points"].mean()

    team_rows = df.merge(joined[["match", "alliance", "opponent_points"]], on=["match", "alliance"], how="left")
    team_rows = team_rows[team_rows.get("defense_played", False) == True]  # noqa: E712
    if team_rows.empty:
        return pd.DataFrame(columns=["team", "defense_suppression"])

    suppression = (
        team_rows.groupby("team", as_index=False)["opponent_points"]
        .mean()
        .assign(defense_suppression=lambda d: (league_opp_avg - d["opponent_points"]).fillna(0))
        [["team", "defense_suppression"]]
    )
    return suppression


def compute_advanced_metrics(team_df: pd.DataFrame, raw_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Compute second-layer advanced metrics with shrinkage and ridge estimation."""
    advanced = team_df.copy()
    suppression = _defense_suppression_from_matches(raw_df)
    advanced = advanced.merge(suppression, on="team", how="left")
    advanced["defense_suppression"] = advanced["defense_suppression"].fillna(0.0)

    advanced["weighted_strength"] = (
        advanced["auto_avg"] * ACTION_WEIGHTS["auto_points"]
        + advanced["teleop_avg"] * ACTION_WEIGHTS["teleop_points"]
        + advanced["fuel_scored_avg"] * ACTION_WEIGHTS["fuel_scored"]
        + advanced["fuel_accuracy"] * ACTION_WEIGHTS["fuel_accuracy"]
        + advanced["climb_avg"] * ACTION_WEIGHTS["climb_points"]
        + advanced["reliability"] * ACTION_WEIGHTS["reliability"]
        + advanced["defense_effectiveness"] * ACTION_WEIGHTS["defense_effectiveness"]
        + advanced["defense_suppression"] * 0.5
        + advanced["cycle_efficiency"] * ACTION_WEIGHTS["cycle_efficiency"]
        + advanced["fouls_avg"] * ACTION_WEIGHTS["foul_penalty"]
    )

    # Decision Quality: rewards efficient shot selection plus low foul tendency.
    volume_stability = np.tanh(advanced["accuracy_volume_index"] / 6.0)
    advanced["decision_quality"] = (
        0.55 * advanced["fuel_accuracy"]
        + 0.25 * np.tanh(advanced["cycle_efficiency"] / 5)
        + 0.2 * (1 - np.tanh(advanced["fouls_avg"]))
        + 0.1 * volume_stability
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
    replacement_level = advanced["points_per_match"].quantile(0.35)
    advanced["value_over_replacement"] = advanced["adjusted_contribution"] - replacement_level
    advanced["pressure_ceiling"] = advanced["ppm_p90"] * (0.6 + 0.4 * advanced["reliability"])
    advanced["opponent_adjusted_contribution"] = (
        advanced["adjusted_contribution"] + 0.35 * advanced["defense_suppression"]
    )

    features = advanced[
        [
            "fuel_scored_avg",
            "cycle_efficiency",
            "climb_avg",
            "reliability",
            "defense_effectiveness",
            "defense_suppression",
        ]
    ].to_numpy()
    y = advanced["weighted_strength"].to_numpy()
    if len(advanced) >= 2:
        beta = _ridge_closed_form(features, y, RIDGE_ALPHA)
        advanced["latent_match_impact"] = features @ beta
    else:
        advanced["latent_match_impact"] = advanced["weighted_strength"]

    advanced["match_readiness_index"] = (
        0.35 * advanced["decision_quality"]
        + 0.25 * advanced["reliability_under_pressure"]
        + 0.25 * advanced["consistency_ceiling_balance"]
        + 0.15 * np.clip(advanced["value_over_replacement"] + 50, 0, 100)
    )

    return advanced.sort_values("latent_match_impact", ascending=False).reset_index(drop=True)
