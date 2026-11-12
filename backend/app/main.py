from __future__ import annotations
from datetime import date
from io import StringIO
import os
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .models import estimate_lambdas, predict
from .analyst import explain

app = FastAPI(title="FMIS API", version="0.1.0", description="CSV-first football probability research API")
origins = os.getenv("FMIS_CORS_ORIGINS", "*").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])
REQUIRED = {"date", "home_team", "away_team", "home_goals", "away_goals"}
DATA: list[dict] = []

class AnalyzeRequest(BaseModel):
    home_team: str = Field(min_length=1, max_length=100)
    away_team: str = Field(min_length=1, max_length=100)
    as_of: date
    total_line: float = Field(default=2.5, ge=0.5, le=8.5)
    handicap_home: float = Field(default=-0.5, ge=-3.0, le=3.0)

@app.get("/api/health")
def health():
    return {"status": "ok", "version": app.version, "matches_loaded": len(DATA)}

@app.post("/api/data/csv")
async def upload_csv(file: UploadFile = File(...)):
    global DATA
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Upload a .csv file")
    raw = await file.read()
    if len(raw) > 10_000_000:
        raise HTTPException(413, "CSV exceeds 10 MB")
    try:
        df = pd.read_csv(StringIO(raw.decode("utf-8-sig")))
        missing = REQUIRED - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
        df["date"] = pd.to_datetime(df["date"], errors="raise").dt.date
        for col in ("home_goals", "away_goals"):
            df[col] = pd.to_numeric(df[col], errors="raise")
            if (df[col] < 0).any() or (df[col] % 1 != 0).any():
                raise ValueError(f"{col} must contain non-negative whole numbers")
        for col in ("home_xg", "away_xg"):
            if col in df:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["date", "home_team", "away_team", "home_goals", "away_goals"])
        # Convert NaN to real None so missing optional xG never contaminates model arithmetic.
        df = df.astype(object).where(pd.notna(df), None)
        DATA = df.to_dict(orient="records")
        return {"loaded": len(DATA), "columns": list(df.columns), "status": "validated"}
    except Exception as exc:
        raise HTTPException(400, f"Invalid CSV: {exc}") from exc

@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    if not DATA:
        raise HTTPException(409, "Upload historical CSV data first")
    prior = [m for m in DATA if m["date"] < req.as_of]
    try:
        lh, la, quality = estimate_lambdas(prior, req.home_team, req.away_team)
        result = predict(lh, la, req.total_line, req.handicap_home)
        result["analyst"] = explain(req.home_team, req.away_team, result, quality)
        result["data_quality"] = {"basis": quality, "prior_matches": len(prior), "as_of": req.as_of.isoformat()}
        return result
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@app.get("/")
def root():
    return {"name": "FMIS", "docs": "/docs", "health": "/api/health"}
