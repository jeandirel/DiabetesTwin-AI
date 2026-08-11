from __future__ import annotations

from fastapi import FastAPI

from diabetestwin.fhir import dataframe_to_fhir_observations
from diabetestwin.metrics import compute_glycemic_metrics
from diabetestwin.models import SimulationPoint, SimulationRequest, SimulationResponse
from diabetestwin.simulator import simulate_day


DISCLAIMER = (
    "Research/education prototype only. Synthetic virtual-patient outputs are not medical advice, "
    "a diagnosis, or a substitute for a validated CGM or clinician."
)

app = FastAPI(
    title="DiabetesTwin-AI API",
    version="0.1.0",
    description="Predictive virtual-patient glucose simulation for research and education.",
)


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
