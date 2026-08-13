from __future__ import annotations

import csv
import math
import random
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from diabetestwin.models import GlycemicMetrics, SimulationPoint, SimulationRequest, SimulationResponse
from diabetestwin.web_dashboard import DASHBOARD_HTML

DISCLAIMER = (
    "Research/education prototype only. Synthetic virtual-patient outputs are not medical advice, "
    "a diagnosis, or a substitute for a validated CGM or clinician."
)
DEMO_CGMACROS_PATH = Path("data/demo/cgmacros_demo.csv")
LOW = 70.0
VERY_LOW = 54.0
HIGH = 180.0
VERY_HIGH = 250.0
MIN_GLUCOSE = 45.0
MAX_GLUCOSE = 400.0

app = FastAPI(
    title="DiabetesTwin-AI API",
    version="0.3.0",
    description="Predictive virtual-patient glucose simulation for research and education.",
)


def _gamma_response(delta_min: float, peak_min: float = 50.0) -> float:
    if delta_min < 0:
        return 0.0
    positive = max(delta_min, 0.0)
    return (positive / peak_min) * math.exp(1.0 - positive / peak_min)


def _exercise_response(delta_min: float, duration_min: int) -> float:
    if delta_min < 0:
        return 0.0
    positive = max(delta_min, 0.0)
    onset = 1.0 - math.exp(-positive / 20.0)
    decay_start = max(positive - max(duration_min, 1), 0.0)
    decay = math.exp(-decay_start / 120.0)
    return onset * decay


def _compute_metrics(values: list[float]) -> GlycemicMetrics:
    if not values:
        raise ValueError("No glucose values available")

    count = len(values)
    mean = sum(values) / count
    variance = sum((value - mean) ** 2 for value in values) / count
    std = math.sqrt(variance)
    cv = 0.0 if mean == 0 else 100.0 * std / mean

    return GlycemicMetrics(
        mean_glucose=round(mean, 1),
        min_glucose=round(min(values), 1),
        max_glucose=round(max(values), 1),
        coefficient_of_variation_pct=round(cv, 1),
        time_in_range_pct=round(100.0 * sum(LOW <= value <= HIGH for value in values) / count, 1),
        time_below_range_pct=round(100.0 * sum(value < LOW for value in values) / count, 1),
        time_above_range_pct=round(100.0 * sum(value > HIGH for value in values) / count, 1),
        time_very_low_pct=round(100.0 * sum(value < VERY_LOW for value in values) / count, 1),
        time_very_high_pct=round(100.0 * sum(value > VERY_HIGH for value in values) / count, 1),
    )


def _simulate(request: SimulationRequest) -> tuple[list[SimulationPoint], GlycemicMetrics]:
    patient = request.patient
    scenario = request.scenario
    minutes = list(range(0, 24 * 60, request.step_minutes))
    hours = [minute / 60.0 for minute in minutes]

    sleep_debt = max(0.0, 7.5 - scenario.sleep_hours)
    sleep_quality_penalty = (1.0 - scenario.sleep_quality) * 10.0 + sleep_debt * 2.2

    glucose: list[float] = []
    for minute, hour in zip(minutes, hours, strict=True):
        circadian = patient.circadian_amplitude * math.sin(2.0 * math.pi * (hour - 4.5) / 24.0)
        value = patient.baseline_glucose + circadian + patient.stress_sensitivity * scenario.stress
        value += sleep_quality_penalty

        for meal in scenario.meals:
            delta = minute - meal.hour * 60.0
            value += meal.carbs_g * patient.carb_sensitivity * _gamma_response(delta)

        for activity in scenario.exercise:
            delta = minute - activity.hour * 60.0
            duration_factor = min(activity.duration_min / 45.0, 1.6)
            amplitude = patient.activity_sensitivity * activity.intensity * duration_factor
            value -= amplitude * _exercise_response(delta, activity.duration_min)

        glucose.append(value)

    rng = random.Random(request.seed)
    innovations = [rng.gauss(0.0, 1.4) for _ in minutes]
    correlated = 0.0
    for index in range(1, len(glucose)):
        correlated = 0.82 * correlated + innovations[index]
        glucose[index] += correlated

    glucose = [round(min(MAX_GLUCOSE, max(MIN_GLUCOSE, value)), 2) for value in glucose]
    points = [
        SimulationPoint(minute=minute, hour=hour, glucose_mg_dl=value)
        for minute, hour, value in zip(minutes, hours, glucose, strict=True)
    ]
    return points, _compute_metrics(glucose)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root() -> HTMLResponse:
    return HTMLResponse(DASHBOARD_HTML)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "DiabetesTwin-AI", "runtime": "lightweight-vercel"}


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest) -> SimulationResponse:
    points, metrics = _simulate(request)
    return SimulationResponse(points=points, metrics=metrics, disclaimer=DISCLAIMER)


@lru_cache(maxsize=1)
def _load_demo_cgmacros() -> list[dict[str, str]]:
    if not DEMO_CGMACROS_PATH.exists():
        raise FileNotFoundError(DEMO_CGMACROS_PATH)

    rows: list[dict[str, str]] = []
    with DEMO_CGMACROS_PATH.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            participant = str(row.get("participant_id", "")).strip().zfill(3)
            timestamp = str(row.get("timestamp", "")).strip()
            glucose = str(row.get("glucose_mg_dl", "")).strip()
            if not participant or not timestamp or not glucose:
                continue
            try:
                datetime.fromisoformat(timestamp)
                float(glucose)
            except ValueError:
                continue
            row["participant_id"] = participant
            rows.append(row)
    rows.sort(key=lambda row: row["timestamp"])
    return rows


@app.get("/demo/cgmacros")
def demo_cgmacros(
    participant_id: str = Query(default="001", min_length=1, max_length=8),
    max_points: int = Query(default=600, ge=100, le=1200),
) -> dict:
    try:
        rows = _load_demo_cgmacros()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Bundled CGMacros demo subset is unavailable.") from exc

    participant = participant_id.strip().zfill(3)
    subset = [row for row in rows if row["participant_id"] == participant]
    if not subset:
        available = sorted({row["participant_id"] for row in rows})
        raise HTTPException(
            status_code=404,
            detail={"message": f"Unknown demo participant: {participant}", "available": available},
        )

    values = [float(row["glucose_mg_dl"]) for row in subset]
    metrics = _compute_metrics(values)
    step = max(1, len(subset) // max_points)
    display = subset[::step]
    diagnosis = subset[0].get("diagnosis", "unknown") or "unknown"
    hba1c_raw = subset[0].get("hba1c", "")
    try:
        hba1c = float(hba1c_raw) if hba1c_raw not in {"", None} else None
    except ValueError:
        hba1c = None

    return {
        "participant_id": participant,
        "diagnosis": diagnosis,
        "diagnosis_label": diagnosis.replace("_", " ").title(),
        "hba1c": hba1c,
        "start": datetime.fromisoformat(subset[0]["timestamp"]).isoformat(),
        "end": datetime.fromisoformat(subset[-1]["timestamp"]).isoformat(),
        "source": "PhysioNet CGMacros v1.0.0 deployment subset",
        "license": "CC BY-NC-SA 4.0",
        "metrics": metrics.model_dump(),
        "points": [
            {
                "timestamp": datetime.fromisoformat(row["timestamp"]).isoformat(),
                "glucose_mg_dl": float(row["glucose_mg_dl"]),
            }
            for row in display
        ],
    }


def _fhir_observations(points: list[SimulationPoint]) -> list[dict]:
    start_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    resources: list[dict] = []
    for point in points:
        timestamp = start_time + timedelta(minutes=point.minute)
        resources.append(
            {
                "resourceType": "Observation",
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "laboratory",
                                "display": "Laboratory",
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "15074-8",
                            "display": "Glucose [Moles/volume] in Blood",
                        }
                    ],
                    "text": "Simulated glucose",
                },
                "subject": {"reference": "Patient/virtual-patient"},
                "effectiveDateTime": timestamp.isoformat(),
                "valueQuantity": {
                    "value": round(point.glucose_mg_dl, 1),
                    "unit": "mg/dL",
                    "system": "http://unitsofmeasure.org",
                    "code": "mg/dL",
                },
                "note": [{"text": "Synthetic observation generated by DiabetesTwin-AI; not a clinical measurement."}],
            }
        )
    return resources


@app.post("/fhir/observations")
def fhir_observations(request: SimulationRequest) -> dict:
    points, _ = _simulate(request)
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": resource} for resource in _fhir_observations(points)],
        "meta": {"tag": [{"display": "Synthetic educational data"}]},
    }
