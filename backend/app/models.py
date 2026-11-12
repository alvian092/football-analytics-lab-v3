"""Transparent football probability models."""
from __future__ import annotations
from math import exp, factorial
from typing import Any
import numpy as np


def poisson_pmf(k: int, lam: float) -> float:
    if k < 0 or lam < 0:
        raise ValueError("k and lambda must be non-negative")
    return exp(-lam) * lam**k / factorial(k)


def estimate_lambdas(matches: list[dict[str, Any]], home: str, away: str) -> tuple[float, float, str]:
    """Estimate expected goals from prior rows only; use xG when enough exists."""
    prior = [m for m in matches if m["home_team"] in (home, away) or m["away_team"] in (home, away)]
    home_rows = [m for m in prior if m["home_team"] == home or m["away_team"] == home]
    away_rows = [m for m in prior if m["home_team"] == away or m["away_team"] == away]
    if len(home_rows) < 3 or len(away_rows) < 3:
        raise ValueError("At least 3 prior matches per team are required")
    def scored_conceded(rows: list[dict[str, Any]], team: str):
        scored, conceded = [], []
        for m in rows:
            is_home = m["home_team"] == team
            scored.append(float(m.get("home_xg") if is_home and m.get("home_xg") is not None else m["home_goals"] if is_home else m.get("away_xg") if m.get("away_xg") is not None else m["away_goals"]))
            conceded.append(float(m.get("away_xg") if is_home and m.get("away_xg") is not None else m["away_goals"] if is_home else m.get("home_xg") if m.get("home_xg") is not None else m["home_goals"]))
        return float(np.mean(scored)), float(np.mean(conceded))
    h_for, h_against = scored_conceded(home_rows, home)
    a_for, a_against = scored_conceded(away_rows, away)
    # Conservative blend of team's attack and opponent's defensive concession rate.
    lam_h = max(0.15, min(4.0, 0.55 * h_for + 0.45 * a_against + 0.12))
    lam_a = max(0.15, min(4.0, 0.55 * a_for + 0.45 * h_against))
    has_xg = any(m.get("home_xg") is not None and m.get("away_xg") is not None for m in prior)
    return lam_h, lam_a, "mixed_xg_and_goals" if has_xg else "goals_only"


def score_matrix(lam_home: float, lam_away: float, max_goals: int = 10, rho: float = 0.0) -> np.ndarray:
    """Independent Poisson matrix with optional Dixon-Coles low-score correction."""
    if lam_home <= 0 or lam_away <= 0 or max_goals < 3:
        raise ValueError("Invalid lambda or score-grid size")
    p_home = np.array([poisson_pmf(i, lam_home) for i in range(max_goals + 1)])
    p_away = np.array([poisson_pmf(i, lam_away) for i in range(max_goals + 1)])
    matrix = np.outer(p_home, p_away)
    if rho:
        matrix[0, 0] *= max(0.01, 1 - lam_home * lam_away * rho)
        matrix[0, 1] *= max(0.01, 1 + lam_home * rho)
        matrix[1, 0] *= max(0.01, 1 + lam_away * rho)
        matrix[1, 1] *= max(0.01, 1 - rho)
    matrix /= matrix.sum()
    return matrix


def market_probabilities(matrix: np.ndarray, total_line: float = 2.5, handicap_home: float = -0.5) -> dict[str, Any]:
    n = matrix.shape[0]
    home = draw = away = over = 0.0
    ah = {"win_full": 0.0, "win_half": 0.0, "push": 0.0, "lose_half": 0.0, "lose_full": 0.0}
    # Quarter handicaps are split into adjacent half/whole lines.
    def settle(diff: int, line: float) -> str:
        result = diff + line
        return "win_full" if result > 1e-9 else "lose_full" if result < -1e-9 else "push"
    for h in range(n):
        for a in range(n):
            p = float(matrix[h, a])
            diff, total = h - a, h + a
            if diff > 0: home += p
            elif diff == 0: draw += p
            else: away += p
            if total > total_line: over += p
            # Split quarter lines into two component lines.
            if abs(handicap_home * 4 - round(handicap_home * 4)) > 1e-8:
                raise ValueError("Handicap must use quarter-goal increments")
            if round(handicap_home * 4) % 2:
                parts = [handicap_home - 0.25, handicap_home + 0.25]
                outcomes = [settle(diff, x) for x in parts]
                if outcomes[0] == outcomes[1]: ah[outcomes[0]] += p
                elif "push" in outcomes: ah["win_half" if "win_full" in outcomes else "lose_half"] += p
                else: ah["win_half" if outcomes.count("win_full") else "lose_half"] += p
            else:
                ah[settle(diff, handicap_home)] += p
    return {"1x2": {"home": home, "draw": draw, "away": away},
            "totals": {"line": total_line, "over": over, "under": 1.0 - over},
            "asian_handicap_home": {"line": handicap_home, **ah}}


def predict(lam_home: float, lam_away: float, total_line: float = 2.5, handicap_home: float = -0.5) -> dict[str, Any]:
    matrix = score_matrix(lam_home, lam_away, rho=-0.08)
    probs = market_probabilities(matrix, total_line, handicap_home)
    flat = [(float(matrix[h, a]), h, a) for h in range(matrix.shape[0]) for a in range(matrix.shape[1])]
    flat.sort(reverse=True)
    return {"expected_goals": {"home": lam_home, "away": lam_away},
            "most_likely_scores": [{"score": f"{h}-{a}", "probability": p} for p, h, a in flat[:5]],
            "markets": probs, "model": "poisson_dixon_coles"}
