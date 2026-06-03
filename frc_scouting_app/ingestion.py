"""CSV ingestion, schema standardization, and data quality checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from frc_scouting_app.config import (
    BOOLEAN_COLUMNS,
    CATEGORICAL_COLUMNS,
    DEFAULT_VALUES,
    NUMERIC_COLUMNS,
    REQUIRED_COLUMNS,
    SCHEMA_ALIASES,
)


@dataclass
class ValidationReport:
    """Container for schema and value quality diagnostics."""

    missing_required: List[str]
    mapped_columns: Dict[str, str]
    suspicious_rows: int
    duplicate_rows_merged: int
    warnings: List[str]


def _normalize_name(column_name: str) -> str:
    """Normalize incoming CSV headers for alias matching."""
    return column_name.strip().lower().replace("-", "_").replace(" ", "_")


def build_column_mapping(columns: List[str]) -> Tuple[Dict[str, str], List[str]]:
    """Map uploaded CSV headers onto the canonical scouting schema."""
    normalized = {_normalize_name(c): c for c in columns}
    mapping: Dict[str, str] = {}
    warnings: List[str] = []

    for canonical, aliases in SCHEMA_ALIASES.items():
        for alias in aliases:
            key = _normalize_name(alias)
            if key in normalized:
                mapping[normalized[key]] = canonical
                break

    unmatched = [c for c in columns if c not in mapping]
    if unmatched:
        warnings.append(f"Unmapped columns retained as extra fields: {', '.join(unmatched)}")

    duplicate_targets = pd.Series(list(mapping.values())).value_counts()
    duplicates = duplicate_targets[duplicate_targets > 1].index.tolist()
    if duplicates:
        warnings.append(f"Multiple source columns mapped to the same fields: {', '.join(duplicates)}")

    return mapping, warnings


def _to_bool(series: pd.Series) -> pd.Series:
    """Convert common scouting checkbox values to booleans."""
    true_vals = {"1", "true", "t", "yes", "y", "checked"}
    false_vals = {"0", "false", "f", "no", "n", "unchecked", ""}

    cleaned = series.fillna("").astype(str).str.strip().str.lower()
    return cleaned.where(cleaned.isin(true_vals | false_vals), "false").isin(true_vals)


def _add_range_warnings(df: pd.DataFrame, warnings: List[str]) -> None:
    """Append basic warnings for values that are probably data-entry mistakes."""
    if "fuel_scored" in df.columns and "fuel_attempted" in df.columns:
        if (df["fuel_scored"] > df["fuel_attempted"]).any():
            warnings.append("Some rows have more fuel scored than fuel attempted.")

    if "cycle_time" in df.columns and (df["cycle_time"] <= 0).any():
        warnings.append("Some rows have zero or negative cycle times.")

    if "team" in df.columns and df["team"].isna().any():
        warnings.append("Some team numbers could not be parsed.")


def load_and_standardize_csv(csv_file) -> Tuple[pd.DataFrame, ValidationReport]:
    """Load CSV, map columns to canonical schema, validate, and aggregate duplicate scouting rows."""
    raw_df = pd.read_csv(csv_file)
    mapping, warnings = build_column_mapping(raw_df.columns.tolist())
    df = raw_df.rename(columns=mapping)

    missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    for column, default in DEFAULT_VALUES.items():
        if column not in df.columns:
            df[column] = default

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in BOOLEAN_COLUMNS:
        if col in df.columns:
            df[col] = _to_bool(df[col])

    for col in CATEGORICAL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()

    if "team" in df.columns:
        df["team"] = df["team"].astype(str).str.extract(r"(\d+)", expand=False)
        df["team"] = pd.to_numeric(df["team"], errors="coerce")

    if "fuel_attempted" in df.columns and "fuel_scored" in df.columns:
        df["fuel_missed"] = (df["fuel_attempted"] - df["fuel_scored"]).clip(lower=0)

    _add_range_warnings(df, warnings)

    suspicious_mask = (
        (df.get("fuel_scored", 0) > df.get("fuel_attempted", np.inf))
        | (df.get("cycle_time", 0) < 0)
        | (df.get("auto_points", 0) < 0)
        | (df.get("teleop_points", 0) < 0)
    )
    suspicious_rows = int(suspicious_mask.sum())

    group_cols = [c for c in ["team", "match", "alliance"] if c in df.columns]
    before = len(df)

    if len(group_cols) == 3:
        aggregations = {
            "auto_points": "mean",
            "teleop_points": "mean",
            "fuel_scored": "mean",
            "fuel_attempted": "mean",
            "fuel_missed": "mean",
            "climb_points": "max",
            "fouls": "mean",
            "breakdown": "max",
            "defense_played": "max",
            "defense_effectiveness": "mean",
            "cycle_time": "mean",
            "endgame_result": "last",
            "match_result": "last",
        }
        present_agg = {k: v for k, v in aggregations.items() if k in df.columns}
        df = df.groupby(group_cols, as_index=False).agg(present_agg)

    duplicate_rows_merged = max(before - len(df), 0)

    for column, default in DEFAULT_VALUES.items():
        if column not in df.columns:
            df[column] = default

    report = ValidationReport(
        missing_required=missing_required,
        mapped_columns={v: k for k, v in mapping.items()},
        suspicious_rows=suspicious_rows,
        duplicate_rows_merged=duplicate_rows_merged,
        warnings=warnings,
    )
    return df, report