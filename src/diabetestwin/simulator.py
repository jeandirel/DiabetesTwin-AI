from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .models import LifestyleScenario, PatientProfile


MIN_GLUCOSE = 45.0
MAX_GLUCOSE = 400.0


def _gamma_response(delta_min: np.ndarray, peak_min: float = 50.0) -> np.ndarray:
    """Smooth positive kernel with a peak around ``peak_min``."""
    positive = np.maximum(delta_min, 0.0)
    response = (positive / peak_min) * np.exp(1.0 - positive / peak_min)
    response[delta_min < 0] = 0.0
    return response


def _exercise_response(delta_min: np.ndarray, duration_min: int) -> np.ndarray:
    """Exercise effect with a gradual onset and post-activity decay."""
    positive = np.maximum(delta_min, 0.0)
    onset = 1.0 - np.exp(-positive / 20.0)
    decay_start = np.maximum(positive - max(duration_min, 1), 0.0)
    decay = np.exp(-decay_start / 120.0)
    response = onset * decay
    response[delta_min < 0] = 0.0
    return response


def simulate_day(
    patient: PatientProfile,
    scenario: LifestyleScenario,
    *,
    seed: int = 42,
    step_minutes: int = 5,
) -> pd.DataFrame:
    """Simulate one day of glucose for a virtual patient.

    This is a physiology-inspired educational model. It is deliberately simple,
    reproducible, and excludes medication/insulin dosing recommendations.
    """
    minutes = np.arange(0, 24 * 60, step_minutes, dtype=int)
    hours = minutes / 60.0

    circadian = patient.circadian_amplitude * np.sin(2 * math.pi * (hours - 4.5) / 24.0)

    stress_offset = patient.stress_sensitivity * scenario.stress
    sleep_debt = max(0.0, 7.5 - scenario.sleep_hours)
    sleep_quality_penalty = (1.0 - scenario.sleep_quality) * 10.0 + sleep_debt * 2.2

    glucose = (
        np.full_like(hours, patient.baseline_glucose, dtype=float)
        + circadian
        + stress_offset
        + sleep_quality_penalty
    )

    for meal in scenario.meals:
        delta = minutes - meal.hour * 60.0
        amplitude = meal.carbs_g * patient.carb_sensitivity
        glucose += amplitude * _gamma_response(delta, peak_min=50.0)

    for activity in scenario.exercise:
        delta = minutes - activity.hour * 60.0
        duration_factor = min(activity.duration_min / 45.0, 1.6)
        amplitude = patient.activity_sensitivity * activity.intensity * duration_factor
        glucose -= amplitude * _exercise_response(delta, activity.duration_min)

    rng = np.random.default_rng(seed)
    innovations = rng.normal(0.0, 1.4, size=len(minutes))
    correlated = np.zeros_like(innovations)
    for i in range(1, len(innovations)):
        correlated[i] = 0.82 * correlated[i - 1] + innovations[i]
    glucose += correlated

    glucose = np.clip(glucose, MIN_GLUCOSE, MAX_GLUCOSE)

    return pd.DataFrame(
        {
            "minute": minutes,
            "hour": hours,
            "glucose_mg_dl": np.round(glucose, 2),
        }
    )


def default_scenario() -> LifestyleScenario:
    from .models import ExerciseEvent, MealEvent

    return LifestyleScenario(
        meals=[
            MealEvent(hour=8.0, carbs_g=45, label="Breakfast"),
            MealEvent(hour=13.0, carbs_g=65, label="Lunch"),
            MealEvent(hour=19.5, carbs_g=70, label="Dinner"),
        ],
        exercise=[ExerciseEvent(hour=18.0, duration_min=35, intensity=0.55, label="Walk")],
        stress=0.25,
        sleep_hours=7.5,
        sleep_quality=0.8,
    )
