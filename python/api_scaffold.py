"""
Part 2 — FastAPI scaffold for PakWheels SVM inference.
Request fields and preprocessing must match training (encoding, column order, scaler).
If only the classifier was saved, also joblib.dump(preprocessor).

Run: uvicorn api_scaffold:app --reload --port 8000
"""

from contextlib import asynccontextmanager

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


MODEL_PATH = "pakwheels_svm_model.pkl"  # or path with spaces from brief — rename for sanity
PREPROCESSOR_PATH = "pakwheels_preprocessor.pkl"  # add if you saved ColumnTransformer separately


class PredictRequest(BaseModel):
    year: int = Field(..., ge=1980, le=2030)
    engine: int = Field(..., description="Engine capacity (cc) — matches brief JSON key 'engine'")
    mileage: int = Field(..., ge=0)
    transmission: str
    fuel: str
    body_type: str | None = None
    city: str | None = None


class PredictResponse(BaseModel):
    price_category: str
    label: int


clf = None
pre = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global clf, pre
    try:
        clf = joblib.load(MODEL_PATH)
    except Exception as e:
        raise RuntimeError(f"Failed to load model: {e}") from e
    try:
        pre = joblib.load(PREPROCESSOR_PATH)
    except FileNotFoundError:
        pre = None  # assume pipeline embedded in clf
    yield


app = FastAPI(title="PakWheels price tier", lifespan=lifespan)


def build_feature_matrix(body: PredictRequest) -> np.ndarray:
    """
    Replace with the same feature construction as training.
    Example only — wrong shape will crash or mis-predict.
    """
    if pre is not None:
        # Typical: pre.transform(DataFrame([[...]], columns=[...]))
        raise NotImplementedError("Wire your preprocessor.transform() here.")
    # Dummy row if pipeline expects raw array (unlikely) — do not use as-is
    return np.array(
        [[body.year, body.engine, body.mileage]],
        dtype=float,
    )


@app.post("/predict", response_model=PredictResponse)
def predict(body: PredictRequest):
    if clf is None:
        raise HTTPException(503, "Model not loaded")
    try:
        X = build_feature_matrix(body)
        y = clf.predict(X)[0]
    except Exception as e:
        raise HTTPException(400, f"Prediction failed: {e}") from e
    label = int(y)
    return PredictResponse(price_category="high" if label == 1 else "low", label=label)


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": clf is not None}
