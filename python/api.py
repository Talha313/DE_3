"""
FastAPI: POST /predict
Loads pickle from train_pakwheels_svm.py (bundle with pipeline + column lists).

Run: uvicorn api:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

MODEL_PATH = os.environ.get("MODEL_PATH", "pakwheels_svm_model.pkl")

_bundle = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bundle
    _bundle = joblib.load(MODEL_PATH)
    yield


app = FastAPI(title="PakWheels SVM", lifespan=lifespan)


class PredictRequest(BaseModel):
    year: int = Field(..., ge=1980, le=2030)
    engine: int = Field(..., description="engine_cc")
    mileage: int = Field(..., ge=0)
    transmission: str
    fuel: str
    body_type: str
    city: str


class PredictResponse(BaseModel):
    price_category: str
    label: int


@app.post("/predict", response_model=PredictResponse)
def predict(body: PredictRequest):
    pipe = _bundle["pipeline"]
    num = _bundle["numeric_cols"]
    cat = _bundle["categorical_cols"]
    row = {}
    if "year" in num:
        row["year"] = body.year
    if "engine_cc" in num:
        row["engine_cc"] = body.engine
    if "mileage_km" in num:
        row["mileage_km"] = body.mileage
    if "transmission" in cat:
        row["transmission"] = body.transmission
    if "fuel_type" in cat:
        row["fuel_type"] = body.fuel
    if "body_type" in cat:
        row["body_type"] = body.body_type
    if "city" in cat:
        row["city"] = body.city
    X = pd.DataFrame([row])
    try:
        y = int(pipe.predict(X)[0])
    except Exception as e:
        raise HTTPException(400, str(e)) from e
    return PredictResponse(price_category="high" if y == 1 else "low", label=y)


@app.get("/health")
def health():
    return {"ok": True, "model": MODEL_PATH}
