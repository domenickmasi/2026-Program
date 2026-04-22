"""Synthetic data generation for local demos when no scouting CSV is uploaded."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_demo_data(seed: int = 2026) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    teams = [111, 254, 971, 1678, 2056, 4414, 3476, 6328, 148, 118, 1619, 4499]
    rows = []
    for match in range(1, 31):
        for team in rng.choice(teams, size=6, replace=False):
            fuel_attempted = int(rng.integers(8, 36))
            fuel_scored = int(min(fuel_attempted, rng.integers(4, fuel_attempted + 1)))
            rows.append(
                {
                    "team": int(team),
                    "match": match,
                    "alliance": "red" if len(rows) % 2 == 0 else "blue",
                    "auto_points": float(rng.integers(0, 20)),
                    "teleop_points": float(rng.integers(10, 55)),
                    "fuel_scored": float(fuel_scored),
                    "fuel_attempted": float(fuel_attempted),
                    "climb_points": float(rng.choice([0, 6, 10, 12], p=[0.15, 0.25, 0.35, 0.25])),
                    "endgame_result": rng.choice(["none", "park", "shallow", "deep"], p=[0.1, 0.2, 0.35, 0.35]),
                    "fouls": float(rng.integers(0, 6)),
                    "breakdown": bool(rng.random() < 0.08),
                    "defense_played": bool(rng.random() < 0.3),
                    "defense_effectiveness": float(rng.integers(0, 7)),
                    "cycle_time": float(rng.uniform(7, 24)),
                    "match_result": rng.choice(["win", "loss"]),
                }
            )
    return pd.DataFrame(rows)
