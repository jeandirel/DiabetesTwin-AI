from __future__ import annotations

import numpy as np
import pandas as pd

from .models import GlycemicMetrics


# ADA 2026 standardized CGM ranges for most adults.
LOW = 70.0
VERY_LOW = 54.0
HIGH = 180.0
VERY_HIGH = 250.0


def compute_glycemic_metrics(data: pd.DataFrame) -> GlycemicMetrics:
    values = data["glucose_mg_dl"].astype(float).to_numpy()
    if values.size == 0:
        raise ValueError("No glucose values available")

    mean = float(np.mean(values))
    std = float(np.std(values))
    cv = 0.0 if mean == 0 else 100.0 * std / mean

    return GlycemicMetrics(
        mean_glucose=round(mean, 1),
        min_glucose=round(float(np.min(values)), 1),
        max_glucose=round(float(np.max(values)), 1),
        coefficient_of_variation_pct=round(cv, 1),
        time_in_range_pct=round(float(np.mean((values >= LOW) & (values <= HIGH)) * 100.0), 1),
        time_below_range_pct=round(float(np.mean(values < LOW) * 100.0), 1),
        time_above_range_pct=round(float(np.mean(values > HIGH) * 100.0), 1),
        time_very_low_pct=round(float(np.mean(values < VERY_LOW) * 100.0), 1),
        time_very_high_pct=round(float(np.mean(values > VERY_HIGH) * 100.0), 1),
    )
