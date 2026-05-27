"""Synthetic data generation for local demos when no scouting CSV is uploaded."""

from __future__ import annotations

import numpy as np
import pandas as pd


# Approximate demo-only team strength values inspired by Statbotics-style EPA.
# These are not live API pulls. They are fixed values so the demo data works offline.
TEAM_STRENGTHS = {
    254: 82,
    1678: 78,
    2056: 76,
    1323: 74,
    2910: 72,
    4414: 70,
    971: 68,
    118: 66,
    148: 65,
    6328: 64,
    1690: 63,
    1619: 62,
    2767: 61,
    5940: 60,
    3476: 59,
    3005: 58,
    1114: 57,
    1538: 56,
    3538: 55,
    604: 54,
    973: 53,
    179: 52,
    33: 51,
    359: 50,
    2337: 49,
    3847: 48,
    4028: 47,
    2168: 46,
    95: 45,
    3310: 44,
    225: 43,
    180: 42,
    5406: 41,
    125: 40,
    1706: 39,
    1717: 38,
    3478: 37,
    4499: 36,
    2655: 35,
    2481: 34,
    1986: 33,
    195: 32,
    1902: 31,
    503: 30,
    1023: 29,
    930: 28,
    3015: 27,
    364: 26,
    1730: 25,
    67: 24,
    27: 23,
    16: 22,
    20: 21,
    40: 20,
    45: 19,
    48: 18,
    56: 17,
    68: 16,
    78: 15,
    85: 14,
    88: 13,
    107: 12,
    111: 11,
    115: 10,
    1257: 9,
    1519: 8,
    1640: 7,
    1747: 6,
    1816: 5,
    1923: 4,
    2220: 3,
    2370: 2,
    2491: 1,
    2607: 0,
    2791: -1,
}


def _scale_strength(strength: float) -> float:
    """Convert a team strength value into a 0 to 1 performance scale."""
    return float(np.clip((strength + 5) / 90, 0.05, 1.0))


def _bounded_normal(rng: np.random.Generator, mean: float, std_dev: float, low: float, high: float) -> float:
    """Sample a normal value and clamp it into a realistic scoring range."""
    return float(np.clip(rng.normal(mean, std_dev), low, high))


def _choose_endgame(rng: np.random.Generator, strength_scale: float) -> tuple[str, float]:
    """Return a rare endgame outcome and its point value."""
    climb_chance = 0.015 + strength_scale * 0.08
    park_chance = 0.08 + strength_scale * 0.08
    roll = rng.random()

    if roll < climb_chance:
        return rng.choice(["shallow", "deep"], p=[0.65, 0.35]), float(rng.choice([6, 10, 12], p=[0.45, 0.35, 0.20]))

    if roll < climb_chance + park_chance:
        return "park", 2.0

    return "none", 0.0


def generate_demo_data(seed: int = 2026) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    teams = list(TEAM_STRENGTHS.keys())
    rows = []

    for match in range(1, 76):
        match_teams = rng.choice(teams, size=6, replace=False)

        for slot, team in enumerate(match_teams):
            strength = TEAM_STRENGTHS[int(team)]
            strength_scale = _scale_strength(strength)

            fuel_attempted = int(
                _bounded_normal(
                    rng,
                    mean=7 + strength_scale * 28,
                    std_dev=4.5,
                    low=1,
                    high=42,
                )
            )

            accuracy = float(np.clip(rng.normal(0.28 + strength_scale * 0.46, 0.09), 0.08, 0.92))
            fuel_scored = int(np.clip(round(fuel_attempted * accuracy), 0, fuel_attempted))

            auto_points = _bounded_normal(
                rng,
                mean=1.5 + strength_scale * 16,
                std_dev=3.0,
                low=0,
                high=24,
            )

            teleop_points = _bounded_normal(
                rng,
                mean=8 + strength_scale * 48,
                std_dev=7.5,
                low=2,
                high=70,
            )

            endgame_result, climb_points = _choose_endgame(rng, strength_scale)
            breakdown_chance = float(np.clip(0.16 - strength_scale * 0.11, 0.025, 0.16))
            defense_chance = float(np.clip(0.18 + (1 - strength_scale) * 0.22, 0.12, 0.45))

            rows.append(
                {
                    "team": int(team),
                    "match": match,
                    "alliance": "red" if slot < 3 else "blue",
                    "auto_points": round(auto_points, 1),
                    "teleop_points": round(teleop_points, 1),
                    "fuel_scored": float(fuel_scored),
                    "fuel_attempted": float(fuel_attempted),
                    "climb_points": climb_points,
                    "endgame_result": endgame_result,
                    "fouls": float(rng.poisson(0.45 + (1 - strength_scale) * 0.7)),
                    "breakdown": bool(rng.random() < breakdown_chance),
                    "defense_played": bool(rng.random() < defense_chance),
                    "defense_effectiveness": round(_bounded_normal(rng, 1 + strength_scale * 4.5, 1.2, 0, 6), 1),
                    "cycle_time": round(_bounded_normal(rng, 23 - strength_scale * 13, 2.6, 6.5, 28), 2),
                    "match_result": rng.choice(["win", "loss"], p=[0.5, 0.5]),
                }
            )

    return pd.DataFrame(rows)