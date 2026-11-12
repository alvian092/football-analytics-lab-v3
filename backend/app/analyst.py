"""Explainable, deterministic Match Analyst; no external AI key required."""
def explain(home: str, away: str, prediction: dict, data_quality: str) -> dict:
    p = prediction["markets"]["1x2"]
    top = max(p, key=p.get)
    labels = {"home": home, "draw": "Draw", "away": away}
    score = prediction["most_likely_scores"][0]["score"]
    notes = [
        f"Highest modeled 1X2 outcome: {labels[top]} ({p[top]:.1%}).",
        f"Most likely exact score in the truncated score grid: {score}.",
        f"Expected goals: {prediction['expected_goals']['home']:.2f}–{prediction['expected_goals']['away']:.2f}.",
        f"Data basis: {data_quality}.",
        "These are model estimates; uncertainty, lineup changes and data coverage can materially alter them."
    ]
    if max(p.values()) < 0.45:
        notes.append("No 1X2 outcome dominates the model; treat the fixture as highly uncertain.")
    return {"headline": f"{home} vs {away}: {labels[top]} is the most likely 1X2 outcome",
            "explanations": notes, "decision": "ANALYSIS_ONLY"}
