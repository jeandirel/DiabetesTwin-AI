from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .models import ExerciseEvent, LifestyleScenario, MealEvent, PatientProfile
from .simulator import simulate_day


@dataclass(frozen=True)
class SyntheticDataset:
    frame: pd.DataFrame
    feature_columns: list[str]
    target_column: str


def _rolling_sum_at_minutes(events: list[tuple[float, float]], minute: np.ndarray, window: int) -> np.ndarray:
    result = np.zeros(len(minute), dtype=float)
    for event_minute, magnitude in events:
        age = minute - event_minute
        result += np.where((age >= 0) & (age <= window), magnitude, 0.0)
    return result


def make_synthetic_training_data(
    patient: PatientProfile,
    *,
    days: int = 28,
    step_minutes: int = 5,
    horizon_minutes: int = 30,
    seed: int = 7,
) -> SyntheticDataset:
    """Generate reproducible virtual-patient data for an ML demonstration."""
    rng = np.random.default_rng(seed)
    frames: list[pd.DataFrame] = []

    for day in range(days):
        meals = [
            MealEvent(hour=float(rng.normal(8.0, 0.35) % 24), carbs_g=float(rng.uniform(30, 65)), label="Breakfast"),
            MealEvent(hour=float(rng.normal(13.0, 0.45) % 24), carbs_g=float(rng.uniform(45, 90)), label="Lunch"),
            MealEvent(hour=float(rng.normal(19.5, 0.55) % 24), carbs_g=float(rng.uniform(45, 95)), label="Dinner"),
        ]
        exercise: list[ExerciseEvent] = []
        if rng.random() < 0.72:
            exercise.append(
                ExerciseEvent(
                    hour=float(rng.uniform(16.5, 20.5)),
                    duration_min=int(rng.integers(20, 61)),
                    intensity=float(rng.uniform(0.35, 0.85)),
                    label="Activity",
                )
            )

        scenario = LifestyleScenario(
            meals=meals,
            exercise=exercise,
            stress=float(rng.uniform(0.05, 0.75)),
            sleep_hours=float(rng.uniform(5.8, 8.8)),
            sleep_quality=float(rng.uniform(0.55, 0.98)),
        )
        day_frame = simulate_day(patient, scenario, seed=seed + day, step_minutes=step_minutes)
        minute = day_frame["minute"].to_numpy()

        day_frame["day"] = day
        day_frame["sin_time"] = np.sin(2 * np.pi * day_frame["hour"] / 24.0)
        day_frame["cos_time"] = np.cos(2 * np.pi * day_frame["hour"] / 24.0)
        day_frame["stress"] = scenario.stress
        day_frame["sleep_hours"] = scenario.sleep_hours
        day_frame["sleep_quality"] = scenario.sleep_quality
        day_frame["carbs_last_120m"] = _rolling_sum_at_minutes(
            [(meal.hour * 60.0, meal.carbs_g) for meal in meals], minute, 120
        )
        day_frame["activity_last_120m"] = _rolling_sum_at_minutes(
            [
                (
                    event.hour * 60.0,
                    event.duration_min * event.intensity,
                )
                for event in exercise
            ],
            minute,
            120,
        )
        day_frame["glucose_lag_15m"] = day_frame["glucose_mg_dl"].shift(15 // step_minutes)
        day_frame["glucose_lag_30m"] = day_frame["glucose_mg_dl"].shift(30 // step_minutes)
        day_frame["target_30m"] = day_frame["glucose_mg_dl"].shift(-(horizon_minutes // step_minutes))
        frames.append(day_frame)

    frame = pd.concat(frames, ignore_index=True).dropna().reset_index(drop=True)
    features = [
        "glucose_mg_dl",
        "glucose_lag_15m",
        "glucose_lag_30m",
        "sin_time",
        "cos_time",
        "carbs_last_120m",
        "activity_last_120m",
        "stress",
        "sleep_hours",
        "sleep_quality",
    ]
    return SyntheticDataset(frame=frame, feature_columns=features, target_column="target_30m")
