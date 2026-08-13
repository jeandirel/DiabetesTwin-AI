"""DiabetesTwin-AI: an educational predictive glucose digital twin."""

from __future__ import annotations

from typing import Any

__all__ = [
    "LifestyleScenario",
    "PatientProfile",
    "compute_glycemic_metrics",
    "default_scenario",
    "simulate_day",
]

__version__ = "0.1.0"


def __getattr__(name: str) -> Any:
    """Lazy public imports to keep serverless application startup lightweight."""
    if name in {"LifestyleScenario", "PatientProfile"}:
        from .models import LifestyleScenario, PatientProfile

        return {"LifestyleScenario": LifestyleScenario, "PatientProfile": PatientProfile}[name]
    if name == "compute_glycemic_metrics":
        from .metrics import compute_glycemic_metrics

        return compute_glycemic_metrics
    if name in {"default_scenario", "simulate_day"}:
        from .simulator import default_scenario, simulate_day

        return {"default_scenario": default_scenario, "simulate_day": simulate_day}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
