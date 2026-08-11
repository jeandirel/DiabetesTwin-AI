from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PatientProfile(BaseModel):
    """Virtual patient parameters for an educational glucose digital twin."""

    name: str = "Virtual Patient"
    age: int = Field(default=45, ge=18, le=90)
    phenotype: Literal["balanced", "insulin_resistant", "active"] = "balanced"
    baseline_glucose: float = Field(default=115.0, ge=70.0, le=220.0)
    carb_sensitivity: float = Field(default=0.75, ge=0.2, le=1.8)
    activity_sensitivity: float = Field(default=18.0, ge=5.0, le=45.0)
    stress_sensitivity: float = Field(default=18.0, ge=0.0, le=40.0)
    circadian_amplitude: float = Field(default=8.0, ge=0.0, le=25.0)

    @classmethod
    def from_phenotype(cls, phenotype: str, *, name: str = "Virtual Patient") -> "PatientProfile":
        presets = {
            "balanced": dict(
                phenotype="balanced",
                baseline_glucose=112.0,
                carb_sensitivity=0.72,
                activity_sensitivity=18.0,
                stress_sensitivity=16.0,
                circadian_amplitude=7.0,
            ),
            "insulin_resistant": dict(
                phenotype="insulin_resistant",
                baseline_glucose=138.0,
                carb_sensitivity=1.05,
                activity_sensitivity=14.0,
                stress_sensitivity=22.0,
                circadian_amplitude=10.0,
            ),
            "active": dict(
                phenotype="active",
                baseline_glucose=102.0,
                carb_sensitivity=0.58,
                activity_sensitivity=24.0,
                stress_sensitivity=13.0,
                circadian_amplitude=6.0,
            ),
        }
        if phenotype not in presets:
            raise ValueError(f"Unknown phenotype: {phenotype}")
        return cls(name=name, **presets[phenotype])


class MealEvent(BaseModel):
    hour: float = Field(ge=0.0, lt=24.0)
    carbs_g: float = Field(ge=0.0, le=250.0)
    label: str = "Meal"


class ExerciseEvent(BaseModel):
    hour: float = Field(ge=0.0, lt=24.0)
    duration_min: int = Field(default=30, ge=0, le=240)
    intensity: float = Field(default=0.55, ge=0.0, le=1.0)
    label: str = "Activity"


class LifestyleScenario(BaseModel):
    meals: list[MealEvent] = Field(default_factory=list)
    exercise: list[ExerciseEvent] = Field(default_factory=list)
    stress: float = Field(default=0.25, ge=0.0, le=1.0)
    sleep_hours: float = Field(default=7.5, ge=3.0, le=12.0)
    sleep_quality: float = Field(default=0.8, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def sort_events(self) -> "LifestyleScenario":
        self.meals = sorted(self.meals, key=lambda event: event.hour)
        self.exercise = sorted(self.exercise, key=lambda event: event.hour)
        return self


class SimulationRequest(BaseModel):
    patient: PatientProfile
    scenario: LifestyleScenario
    seed: int = 42
    step_minutes: int = Field(default=5, ge=1, le=30)


class SimulationPoint(BaseModel):
    minute: int
    hour: float
    glucose_mg_dl: float


class GlycemicMetrics(BaseModel):
    mean_glucose: float
    min_glucose: float
    max_glucose: float
    coefficient_of_variation_pct: float
    time_in_range_pct: float
    time_below_range_pct: float
    time_above_range_pct: float
    time_very_low_pct: float
    time_very_high_pct: float


class SimulationResponse(BaseModel):
    points: list[SimulationPoint]
    metrics: GlycemicMetrics
    disclaimer: str
