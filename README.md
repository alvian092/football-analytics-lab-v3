# FMIS — Football Match Intelligence System

Open, CSV-first football analytics for research and probability education. FMIS estimates 1X2, totals and Asian Handicap probabilities from historical match data. It does **not** guarantee outcomes or provide betting instructions.

## Current scope (v0.1 foundation)
- CSV upload and validation
- Poisson score matrix with optional Dixon–Coles low-score adjustment
- 1X2, Over/Under and Asian Handicap settlement probabilities
- Explainable, deterministic Match Analyst (no paid AI key required)
- FastAPI backend, static dashboard, pytest and GitHub Actions
- Optional live-data adapter interface; provider coverage is not universal

## Data contract
Required CSV columns: `date,home_team,away_team,home_goals,away_goals`.
Optional: `competition,home_xg,away_xg`. Dates must be ISO `YYYY-MM-DD`. xG is never fabricated. Without xG, goal-based estimates are used and marked accordingly.

## Run locally
```bash
python -m venv .venv
# activate the environment, then:
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```
Open http://127.0.0.1:8000. API docs: http://127.0.0.1:8000/docs

Run tests:
```bash
pytest -q
```

## Deploy
- Backend: deploy this repository to Render using `render.yaml`. Free-tier availability and sleep/cold-start behavior depend on the provider's current plan.
- Dashboard: GitHub Actions publishes `frontend/` to GitHub Pages. Enable Pages with **GitHub Actions** as the build source in repository settings.
- Set `FMIS_API_BASE` in `frontend/config.js` to the deployed backend URL (no trailing slash), then commit the change.

## Safety and model governance
- Probabilities are estimates, not certainties.
- Incomplete or stale data must be disclosed; unsupported fixtures return an error.
- No staking, bankroll, or automated wagering functionality.
- Evaluate with chronological/walk-forward splits, Brier score, log loss and calibration before using a model operationally.
- The built-in analyst is rule-based and transparent. A generative AI provider can be added later behind a server-side secret; never expose API keys in browser code.

## License
MIT
