"""DiabetesTwin-AI: an educational predictive glucose digital twin."""

from .metrics import compute_glycemic_metrics
from .models import LifestyleScenario, PatientProfile
from .simulator import default_scenario, simulate_day

__all__ = [
    "LifestyleScenario",
    "PatientProfile",
    "compute_glycemic_metrics",
    "default_scenario",
    "simulate_day",
]

__version__ = "0.1.0"
