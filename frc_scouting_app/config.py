"""Central configuration for metric weighting, schema aliases, and defaults."""

from __future__ import annotations

APP_TITLE = "2026 FRC Scouting Dashboard"
APP_SUBTITLE = "Team performance, picklist comparison, and match prediction tools"
DEFAULT_EVENT_NAME = "2026 Event"
DEFAULT_PAGE_ICON = "🤖"

TEAM_COLUMN = "team"
MATCH_COLUMN = "match"
ALLIANCE_COLUMN = "alliance"

SCHEMA_ALIASES = {
    "team": ["team", "team_number", "team_num", "frc_team", "team id"],
    "match": ["match", "match_number", "match_num", "qm"],
    "alliance": ["alliance", "alliance_color", "color", "side"],
    "auto_points": ["auto_points", "auto_score", "autonomous_points"],
    "teleop_points": ["teleop_points", "teleop_score", "tele_points"],
    "fuel_scored": ["fuel_scored", "shots_made", "cargo_scored"],
    "fuel_attempted": ["fuel_attempted", "shots_attempted", "cargo_attempted"],
    "climb_points": ["climb_points", "endgame_points", "hang_points"],
    "endgame_result": ["endgame_result", "endgame", "climb_result"],
    "fouls": ["fouls", "penalties", "foul_points_given"],
    "breakdown": ["breakdown", "disabled", "robot_breakdown"],
    "defense_played": ["defense_played", "played_defense", "defense"],
    "defense_effectiveness": ["defense_effectiveness", "def_eff", "defense_rating"],
    "cycle_time": ["cycle_time", "avg_cycle_time", "seconds_per_cycle"],
    "match_result": ["match_result", "won", "result"],
}

REQUIRED_COLUMNS = [
    "team",
    "match",
    "alliance",
    "auto_points",
    "teleop_points",
    "fuel_scored",
    "fuel_attempted",
]

NUMERIC_COLUMNS = [
    "team",
    "match",
    "auto_points",
    "teleop_points",
    "fuel_scored",
    "fuel_attempted",
    "climb_points",
    "fouls",
    "defense_effectiveness",
    "cycle_time",
]

BOOLEAN_COLUMNS = ["breakdown", "defense_played"]

CATEGORICAL_COLUMNS = ["alliance", "endgame_result", "match_result"]

DEFAULT_VALUES = {
    "climb_points": 0.0,
    "fouls": 0.0,
    "breakdown": False,
    "defense_played": False,
    "defense_effectiveness": 0.0,
    "cycle_time": 15.0,
    "endgame_result": "none",
    "match_result": "unknown",
}

ACTION_WEIGHTS = {
    "auto_points": 1.35,
    "teleop_points": 1.0,
    "fuel_scored": 0.3,
    "fuel_accuracy": 18.0,
    "climb_points": 1.4,
    "reliability": 14.0,
    "defense_effectiveness": 0.8,
    "cycle_efficiency": 0.4,
    "foul_penalty": -0.8,
}

PICKLIST_SCORE_COLUMNS = [
    "team",
    "matches_played",
    "weighted_score",
    "avg_total_points",
    "fuel_accuracy",
    "reliability_score",
]

MATCH_PREDICTION_COLUMNS = [
    "team",
    "weighted_score",
    "avg_total_points",
    "avg_auto_points",
    "avg_teleop_points",
    "avg_climb_points",
]

RIDGE_ALPHA = 2.5
MIN_MATCH_SAMPLE = 3
DEFAULT_ROUND_DIGITS = 2

DARK_THEME = {
    "paper_bgcolor": "#0E1117",
    "plot_bgcolor": "#0E1117",
    "font": {"color": "#E5E7EB", "size": 14},
    "title": {"font": {"size": 22}},
}


def get_schema_aliases(column_name: str) -> list[str]:
    """Return accepted CSV header names for a standardized scouting column."""
    return SCHEMA_ALIASES.get(column_name, [column_name])