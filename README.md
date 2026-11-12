# FMIS — Football Match Intelligence System

Open, CSV-first football analytics for research and probability education. FMIS estimates 1X2, totals and Asian Handicap probabilities from historical match data. It does not guarantee outcomes or provide betting instructions.

## Current scope (v0.1.1 repair)
- CSV upload and validation with admin-token protection
- Poisson score matrix with Dixon-Coles low-score adjustment
- 1X2 probabilities and full/half/push settlement probabilities for quarter-goal totals and Asian Handicap lines
- Explainable deterministic Match Analyst (no paid AI key required)
- FastAPI backend, static dashboard, pytest and GitHub Actions

## Data contract
Required CSV columns: date,home_team,away_team,home_goals,away_goals.
Optional: competition,home_xg,away_xg. Dates should be ISO YYYY-MM-DD. xG is never fabricated. Missing xG falls back to goals and the model labels its data basis.

## Run locally
    python -m venv .venv
    pip install -r requirements.txt
    uvicorn backend.app.main:app --reload

Open http://127.0.0.1:8000. API docs: http://127.0.0.1:8000/docs

Run tests:
    python -m pytest -q

## Deploy
- Set a strong random FMIS_ADMIN_TOKEN in the backend hosting environment before public deployment. CSV replacement requires this token; public analysis remains read-only.
- Backend: deploy using render.yaml. Free-tier availability and cold starts depend on the provider plan.
- Dashboard: enable GitHub Pages with GitHub Actions as source.
- Set FMIS_API_BASE in frontend/config.js to the deployed backend URL (no trailing slash).
- CSV data currently resides in process memory and is lost on restart; persistent database support is a next milestone, so do not treat a free ephemeral instance as production storage.

## Model governance
- Probabilities are estimates, not certainties.
- Evaluate with chronological/walk-forward splits, Brier score, log loss and calibration before operational use.
- The built-in analyst is rule-based and transparent. A generative AI provider can be added later behind a server-side secret; never expose API keys in browser code.
- No staking, bankroll, or automated wagering functionality.

## License
MIT
