from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from diabetestwin.fhir import dataframe_to_fhir_observations
from diabetestwin.metrics import compute_glycemic_metrics
from diabetestwin.models import SimulationPoint, SimulationRequest, SimulationResponse
from diabetestwin.simulator import simulate_day
from diabetestwin.web_dashboard import DASHBOARD_HTML

DISCLAIMER = (
    "Research/education prototype only. Synthetic virtual-patient outputs are not medical advice, "
    "a diagnosis, or a substitute for a validated CGM or clinician."
)
DEMO_CGMACROS_PATH = Path("data/demo/cgmacros_demo.csv")

app = FastAPI(
    title="DiabetesTwin-AI API",
    version="0.2.0",
    description="Predictive virtual-patient glucose simulation for research and education.",
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root() -> HTMLResponse:
    return HTMLResponse(DASHBOARD_HTML)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "DiabetesTwin-AI"}


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest) -> SimulationResponse:
    frame = simulate_day(
        request.patient,
        request.scenario,
        seed=request.seed,
        step_minutes=request.step_minutes,
    )
    metrics = compute_glycemic_metrics(frame)
    points = [SimulationPoint(**row) for row in frame.to_dict(orient="records")]
    return SimulationResponse(points=points, metrics=metrics, disclaimer=DISCLAIMER)


@lru_cache(maxsize=1)
def _load_demo_cgmacros() -> pd.DataFrame:
    if not DEMO_CGMACROS_PATH.exists():
        raise FileNotFoundError(DEMO_CGMACROS_PATH)
    frame = pd.read_csv(DEMO_CGMACROS_PATH)
    frame["participant_id"] = frame["participant_id"].astype(str).str.zfill(3)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    return frame.dropna(subset=["timestamp", "glucose_mg_dl"]).sort_values("timestamp").reset_index(drop=True)


@app.get("/demo/cgmacros")
def demo_cgmacros(
    participant_id: str = Query(default="001", min_length=1, max_length=8),
    max_points: int = Query(default=600, ge=100, le=1200),
) -> dict:
    try:
        frame = _load_demo_cgmacros()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Bundled CGMacros demo subset is unavailable.") from exc

    participant = participant_id.strip().zfill(3)
    subset = frame[frame["participant_id"] == participant].copy()
    if subset.empty:
        available = sorted(frame["participant_id"].dropna().unique().tolist())
        raise HTTPException(
            status_code=404,
            detail={"message": f"Unknown demo participant: {participant}", "available": available},
        )

    subset = subset.sort_values("timestamp").reset_index(drop=True)
    metrics = compute_glycemic_metrics(subset[["glucose_mg_dl"]])
    step = max(1, len(subset) // max_points)
    display = subset.iloc[::step].copy()
    diagnosis = str(subset["diagnosis"].iloc[0]) if "diagnosis" in subset.columns else "unknown"
    hba1c = subset["hba1c"].iloc[0] if "hba1c" in subset.columns else None

    return {
        "participant_id": participant,
        "diagnosis": diagnosis,
        "diagnosis_label": diagnosis.replace("_", " ").title(),
        "hba1c": None if pd.isna(hba1c) else float(hba1c),
        "start": subset["timestamp"].iloc[0].isoformat(),
        "end": subset["timestamp"].iloc[-1].isoformat(),
        "source": "PhysioNet CGMacros v1.0.0 deployment subset",
        "license": "CC BY-NC-SA 4.0",
        "metrics": metrics.model_dump(),
        "points": [
            {
                "timestamp": row.timestamp.isoformat(),
                "glucose_mg_dl": float(row.glucose_mg_dl),
            }
            for row in display.itertuples(index=False)
        ],
    }


@app.post("/fhir/observations")
def fhir_observations(request: SimulationRequest) -> dict:
    frame = simulate_day(
        request.patient,
        request.scenario,
        seed=request.seed,
        step_minutes=request.step_minutes,
    )
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": resource} for resource in dataframe_to_fhir_observations(frame)],
        "meta": {"tag": [{"display": "Synthetic educational data"}]},
    }
