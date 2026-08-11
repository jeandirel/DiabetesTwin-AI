import pandas as pd

from diabetestwin.metrics import compute_glycemic_metrics


def test_glycemic_metrics_ranges():
    frame = pd.DataFrame({"glucose_mg_dl": [50, 60, 80, 100, 170, 190, 260]})
    metrics = compute_glycemic_metrics(frame)
    assert metrics.time_in_range_pct == 42.9
    assert metrics.time_below_range_pct == 28.6
    assert metrics.time_above_range_pct == 28.6
    assert metrics.time_very_low_pct == 14.3
    assert metrics.time_very_high_pct == 14.3
