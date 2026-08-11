from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from diabetestwin.cgmacros import load_cgmacros_dataset
from diabetestwin.real_predictor import train_grouped_real_predictor, train_personalized_real_predictor


def _write_fixture(root: Path, participants: int = 4, rows: int = 96) -> Path:
    start = pd.Timestamp("2025-01-01 06:00:00")
    bio_rows = []

    for index in range(1, participants + 1):
        participant_id = f"{index:03d}"
        folder = root / f"CGMacros-{participant_id}"
        folder.mkdir(parents=True, exist_ok=True)
        timestamp = pd.date_range(start + pd.Timedelta(days=index), periods=rows, freq="5min")
        phase = np.linspace(0.0, 5.0, rows)
        glucose = 95.0 + index * 8.0 + 12.0 * np.sin(phase) + np.linspace(0.0, 4.0, rows)

        frame = pd.DataFrame(
            {
                "Timestamp": timestamp.strftime("%m/%d/%Y %H:%M"),
                "Libre GL": glucose,
                "Dexcom GL": glucose + 1.5,
                "HR": 65.0 + 3.0 * np.cos(phase),
                "Calories (Activity)": np.full(rows, 1.2),
                "Mets": np.full(rows, 18.0),
                "Meal Type": [None] * rows,
                "Calories": [np.nan] * rows,
                "Carbs": [np.nan] * rows,
                "Protein": [np.nan] * rows,
                "Fat": [np.nan] * rows,
                "Fiber": [np.nan] * rows,
                "Amount Consumed": [np.nan] * rows,
                "Image Path": [None] * rows,
            }
        )
        for row_index, meal in [(12, "Breakfast"), (55, "Lunch")]:
            frame.loc[row_index, "Meal Type"] = meal
            frame.loc[row_index, ["Calories", "Carbs", "Protein", "Fat", "Fiber"]] = [500, 55, 24, 18, 8]
            frame.loc[row_index, "Amount Consumed"] = 100
        frame.to_csv(folder / f"CGMacros-{participant_id}.csv", index=False)

        bio_rows.append(
            {
                "Age": 30 + index,
                "Gender": "M" if index % 2 else "F",
                "BMI": 23.0 + index,
                "A1c PDL (Lab)": 5.2 + 0.5 * index,
                "Fasting GLU - PDL (Lab)": 85 + index * 8,
                "Insulin ": 8.0 + index,
            }
        )

    pd.DataFrame(bio_rows).to_csv(root / "bio.csv", index=False)
    return root


def test_load_real_cgmacros_dataset(tmp_path: Path):
    root = _write_fixture(tmp_path)
    dataset = load_cgmacros_dataset(root, glucose_source="dexcom")

    assert dataset.glucose_source == "dexcom"
    assert dataset.participants == ["001", "002", "003", "004"]
    assert len(dataset.frame) > 200
    assert dataset.target_column == "target_30m"
    assert dataset.frame["carbs_last_120m"].max() >= 55
    assert set(dataset.frame["diagnosis"].unique()) <= {"healthy", "prediabetes", "type2_diabetes"}


def test_real_models_use_non_leaking_splits(tmp_path: Path):
    dataset = load_cgmacros_dataset(_write_fixture(tmp_path), glucose_source="dexcom")

    grouped = train_grouped_real_predictor(dataset, model_name="hgb", seed=3)
    assert grouped.evaluation.split_strategy == "participant_holdout"
    assert grouped.evaluation.train_participants + grouped.evaluation.test_participants == 4
    assert grouped.evaluation.mae_mg_dl >= 0

    personalized = train_personalized_real_predictor(dataset, "001", model_name="hgb", seed=3)
    assert personalized.evaluation.split_strategy == "within_patient_chronological"
    assert personalized.evaluation.train_participants == 1
    assert personalized.predictions["participant_id"].nunique() == 1
