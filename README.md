# FRC 2026 Scouting Analytics & Match Prediction

A local-first Streamlit app for ingesting scouting CSVs, validating schema quality, computing interpretable team metrics, and generating early-stage alliance match predictions.

## What this app does

- Ingests raw scouting CSV files.
- Standardizes inconsistent column names via alias mapping.
- Validates required schema fields and flags suspicious values.
- Aggregates duplicate team/match rows to prevent metric inflation.
- Blocks processing when required schema fields are missing and surfaces explicit error messages.
- Computes simple per-team scouting metrics.
- Computes advanced interpretable metrics including a ridge-estimated latent impact score.
- Computes opponent-adjusted and readiness-oriented advanced metrics (defense suppression, value over replacement, pressure ceiling, match readiness index).
- Supports side-by-side picklist comparison.
- Produces early-stage red-vs-blue alliance predictions with explanation, margin projection, and Monte Carlo uncertainty bands.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Expected input format

The app maps many aliases to canonical fields. Canonical expected fields are:

- `team` (required)
- `match` (required)
- `alliance` (required)
- `auto_points` (required)
- `teleop_points` (required)
- `fuel_scored` (required)
- `fuel_attempted` (required)
- `climb_points`
- `endgame_result`
- `fouls`
- `breakdown`
- `defense_played`
- `defense_effectiveness`
- `cycle_time`
- `match_result`

If optional fields are missing, defaults are injected and surfaced in Data Health warnings.

See `data/sample_scouting_template.csv` for a starter template.

## Page guide

1. **Overview**
   - Event KPIs, top-team leaderboard by selected metric, scoring profile scatter.
2. **Team Detail**
   - Match-by-match phase scoring, fuel makes/attempts trend, advanced metric context.
3. **Picklist / Comparison**
   - Sortable ranked table and side-by-side team comparison panel.
4. **Match Prediction**
   - Select three red and three blue teams; view projected strengths, margin, deterministic/simulated win proxy, confidence bands, and driver factors.
5. **Data Health / Validation**
   - Missing required fields, suspicious values, duplicate-merge count, null audit.
6. **Metric Dictionary**
   - Formula/logic and plain-English explanation for simple and advanced metrics.

## Advanced metric definitions

- **Decision Quality**: weighted blend of shot accuracy, cycle pace, and foul discipline.
- **Reliability Under Pressure**: uptime weighted by consistency (volatility penalty).
- **Adjusted Contribution**: sample-size shrinkage of points contribution.
- **Consistency/Ceiling Balance**: average output relative to peak output.
- **Latent Match Impact (estimated)**:
  - Uses ridge-style regularized linear estimation.
  - Feature inputs: fuel scoring, cycle efficiency, climb value, reliability, defense effectiveness, defense suppression.
  - Output is an **estimated impact proxy**, not objective truth.
- **Defense Suppression**:
  - Compares opponent alliance output in matches where a team recorded defense against event average opponent output.
  - Positive values indicate directional evidence of defensive suppression.
- **Match Readiness Index**:
  - Composite of decision quality, reliability under pressure, consistency/ceiling balance, and value over replacement.
  - Intended to support short-horizon lineup and playoff strategy decisions.

## Current limitations

- Model is early-stage and does not include schedule-strength correction.
- Opponent-adjusted effects are represented approximately via defensive variables, not full possession models.
- Missing or low-quality raw scouting data can materially bias outputs.
- Teams with no historical rows in the loaded dataset are treated as unknown in match prediction and flagged in UI.
- Win probability is a proxy logistic transform of modeled alliance strength difference.
- Simulated confidence ranges assume near-Gaussian score noise and are not calibrated to official FRC scoring distributions.

## Architecture notes

- Python-only implementation today.
- Processing modules are isolated so an R-based modeling package can be plugged in later via a dedicated service/module boundary.
