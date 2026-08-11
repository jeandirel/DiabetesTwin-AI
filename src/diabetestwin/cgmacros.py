from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

CGMACROS_VERSION = "1.0.0"
CGMACROS_DOI = "10.13026/3z8q-x658"
CGMACROS_LICENSE = "CC BY-NC-SA 4.0"

_PARTICIPANT_RE = re.compile(r"CGMacros-(\d{3})\.csv$", re.IGNORECASE)


@dataclass(frozen=True)
class CGMacrosDataset:
    frame: pd.DataFrame
    feature_columns: list[str]
    target_column: str
    glucose_source: str
    horizon_minutes: int

    @property
    def participants(self) -> list[str]:
        values = self.frame["participant_id"].dropna().astype(str).str.zfill(3)
        return sorted(values.unique().tolist())


def _clean_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result.columns = [str(column).lstrip("\ufeff").strip() for column in result.columns]
    return result


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(r"[^0-9eE+\-.]", "", regex=True),
        errors="coerce",
    )


def _parse_timestamps(series: pd.Series) -> pd.Series:
    try:
        return pd.to_datetime(series, errors="coerce", format="mixed")
    except TypeError:
        return pd.to_datetime(series, errors="coerce")


def _participant_id(path: Path) -> str:
    match = _PARTICIPANT_RE.search(path.name)
    if not match:
        raise ValueError(f"Cannot infer participant ID from {path}")
    return match.group(1)


def discover_participant_files(root: str | Path) -> list[Path]:
    root_path = Path(root)
    files = []
    for path in root_path.rglob("CGMacros-*.csv"):
        if _PARTICIPANT_RE.search(path.name):
            files.append(path)
    return sorted(files, key=_participant_id)


def _find_bio_file(root: Path) -> Path | None:
    candidates = [path for path in root.rglob("bio.csv") if path.is_file()]
    return sorted(candidates)[0] if candidates else None


def _diagnosis_from_hba1c(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "unknown"
    numeric = float(value)
    if numeric < 5.7:
        return "healthy"
    if numeric <= 6.4:
        return "prediabetes"
    return "type2_diabetes"


def _bio_rows_by_participant(
    root: Path,
    participant_ids: list[str],
) -> dict[str, dict[str, object]]:
    bio_path = _find_bio_file(root)
    if bio_path is None:
        return {participant_id: {} for participant_id in participant_ids}

    bio = _clean_columns(pd.read_csv(bio_path, low_memory=False)).reset_index(drop=True)
    id_candidates = ["Participant", "Participant ID", "Subject", "Subject ID", "ID", "sub"]
    id_column = next((column for column in id_candidates if column in bio.columns), None)

    rows: dict[str, dict[str, object]] = {}
    if id_column is not None:
        for _, row in bio.iterrows():
            raw_id = str(row[id_column])
            match = re.search(r"(\d{1,3})", raw_id)
            if match:
                rows[match.group(1).zfill(3)] = row.to_dict()
    else:
        # The reference CGMacros notebook aligns sorted participant folders with bio.csv row order.
        for participant_id, (_, row) in zip(participant_ids, bio.iterrows(), strict=False):
            rows[participant_id] = row.to_dict()

    return {participant_id: rows.get(participant_id, {}) for participant_id in participant_ids}


def _static_value(row: dict[str, object], *names: str) -> float:
    for name in names:
        if name in row:
            value = pd.Series([row[name]])
            return float(_numeric(value).iloc[0])
    return float("nan")


def _rolling_event_sum(
    timestamps: pd.Series,
    events: pd.DataFrame,
    value_column: str,
    *,
    window_minutes: int,
) -> np.ndarray:
    result = np.zeros(len(timestamps), dtype=float)
    if events.empty or value_column not in events.columns:
        return result

    event_values = _numeric(events[value_column])
    valid = events["Timestamp"].notna() & event_values.notna()
    for event_time, magnitude in zip(
        events.loc[valid, "Timestamp"],
        event_values.loc[valid],
        strict=False,
    ):
        age = (timestamps - event_time).dt.total_seconds() / 60.0
        result += np.where(
            (age >= 0.0) & (age <= window_minutes),
            float(magnitude),
            0.0,
        )
    return result


def _pick_glucose_column(frame: pd.DataFrame, glucose_source: str) -> tuple[str, str]:
    requested = glucose_source.lower().strip()
    if requested not in {"dexcom", "libre", "auto"}:
        raise ValueError("glucose_source must be one of: dexcom, libre, auto")

    if requested in {"dexcom", "auto"} and "Dexcom GL" in frame.columns:
        if _numeric(frame["Dexcom GL"]).notna().any():
            return "Dexcom GL", "dexcom"
    if "Libre GL" in frame.columns and _numeric(frame["Libre GL"]).notna().any():
        return "Libre GL", "libre"
    raise ValueError("No usable Dexcom GL or Libre GL column found")


def _sampling_interval_minutes(timestamps: pd.Series) -> float:
    gaps = timestamps.diff().dt.total_seconds().div(60.0)
    gaps = gaps[(gaps > 0.0) & (gaps <= 30.0)]
    if gaps.empty:
        raise ValueError("Cannot infer CGMacros sampling interval")
    return float(gaps.median())


def _sensor_column(selected: pd.DataFrame, *candidates: str) -> np.ndarray:
    for column in candidates:
        if column in selected.columns:
            return _numeric(selected[column]).to_numpy()
    return np.full(len(selected), np.nan, dtype=float)


def load_participant(
    path: str | Path,
    *,
    bio_row: dict[str, object] | None = None,
    glucose_source: str = "dexcom",
    horizon_minutes: int = 30,
) -> tuple[pd.DataFrame, str]:
    csv_path = Path(path)
    participant_id = _participant_id(csv_path)
    raw = _clean_columns(pd.read_csv(csv_path, low_memory=False))
    if "Timestamp" not in raw.columns:
        raise ValueError(f"Timestamp column missing from {csv_path}")

    raw["Timestamp"] = _parse_timestamps(raw["Timestamp"])
    raw = raw.dropna(subset=["Timestamp"]).sort_values("Timestamp").reset_index(drop=True)
    glucose_column, resolved_source = _pick_glucose_column(raw, glucose_source)
    glucose = _numeric(raw[glucose_column])

    selected = raw.loc[glucose.notna()].copy()
    selected["glucose_mg_dl"] = glucose.loc[glucose.notna()].astype(float).to_numpy()
    selected = (
        selected.drop_duplicates(subset=["Timestamp"])
        .sort_values("Timestamp")
        .reset_index(drop=True)
    )
    if len(selected) < 60:
        return pd.DataFrame(), resolved_source

    # CGMacros' released, merged participant CSVs are aligned to a one-minute timeline.
    # Infer the cadence from the released file instead of assuming the native CGM cadence.
    sampling_minutes = _sampling_interval_minutes(selected["Timestamp"])

    meal_mask = pd.Series(False, index=raw.index)
    if "Meal Type" in raw.columns:
        meal_mask |= raw["Meal Type"].notna() & raw["Meal Type"].astype(str).str.strip().ne("")
    if "Carbs" in raw.columns:
        meal_mask |= _numeric(raw["Carbs"]).notna()
    meal_events = raw.loc[meal_mask].copy()

    frame = pd.DataFrame(
        {
            "participant_id": participant_id,
            "timestamp": selected["Timestamp"],
            "glucose_mg_dl": selected["glucose_mg_dl"],
        }
    )
    frame["hour"] = frame["timestamp"].dt.hour + frame["timestamp"].dt.minute / 60.0
    frame["sin_time"] = np.sin(2.0 * np.pi * frame["hour"] / 24.0)
    frame["cos_time"] = np.cos(2.0 * np.pi * frame["hour"] / 24.0)

    for output, source in [
        ("carbs_last_120m", "Carbs"),
        ("protein_last_120m", "Protein"),
        ("fat_last_120m", "Fat"),
        ("fiber_last_120m", "Fiber"),
    ]:
        frame[output] = _rolling_event_sum(
            frame["timestamp"],
            meal_events,
            source,
            window_minutes=120,
        )

    frame["heart_rate"] = _sensor_column(selected, "HR")
    frame["mets"] = _sensor_column(selected, "METs", "Mets")
    frame["activity_calories"] = _sensor_column(selected, "Calories (Activity)")

    indexed = frame.set_index("timestamp")
    frame["heart_rate_mean_30m"] = (
        indexed["heart_rate"].rolling("30min", min_periods=1).mean().to_numpy()
    )
    frame["mets_mean_60m"] = (
        indexed["mets"].rolling("60min", min_periods=1).mean().to_numpy()
    )
    frame["activity_calories_60m"] = (
        indexed["activity_calories"].rolling("60min", min_periods=1).sum().to_numpy()
    )

    row = bio_row or {}
    frame["age"] = _static_value(row, "Age")
    frame["bmi"] = _static_value(row, "BMI")
    frame["hba1c"] = _static_value(row, "A1c PDL (Lab)", "A1c")
    frame["fasting_glucose"] = _static_value(
        row,
        "Fasting GLU - PDL (Lab)",
        "Fasting BG",
    )
    frame["fasting_insulin"] = _static_value(row, "Insulin", "Insulin ")
    frame["diagnosis"] = _diagnosis_from_hba1c(frame["hba1c"].iloc[0])

    lag_15_steps = max(1, round(15 / sampling_minutes))
    lag_30_steps = max(1, round(30 / sampling_minutes))
    horizon_steps = max(1, round(horizon_minutes / sampling_minutes))

    frame["glucose_lag_15m"] = frame["glucose_mg_dl"].shift(lag_15_steps)
    frame["glucose_lag_30m"] = frame["glucose_mg_dl"].shift(lag_30_steps)
    frame["glucose_delta_15m"] = frame["glucose_mg_dl"] - frame["glucose_lag_15m"]
    frame["target_30m"] = frame["glucose_mg_dl"].shift(-horizon_steps)

    lag_15_timestamp = frame["timestamp"].shift(lag_15_steps)
    lag_30_timestamp = frame["timestamp"].shift(lag_30_steps)
    frame["target_timestamp"] = frame["timestamp"].shift(-horizon_steps)

    lag_15_actual = (frame["timestamp"] - lag_15_timestamp).dt.total_seconds() / 60.0
    lag_30_actual = (frame["timestamp"] - lag_30_timestamp).dt.total_seconds() / 60.0
    target_actual = (frame["target_timestamp"] - frame["timestamp"]).dt.total_seconds() / 60.0

    tolerance = max(2.0, sampling_minutes * 2.0)
    valid_timing = (
        (lag_15_actual - 15.0).abs() <= tolerance
    ) & (
        (lag_30_actual - 30.0).abs() <= tolerance
    ) & (
        (target_actual - float(horizon_minutes)).abs() <= tolerance
    )
    frame = frame[valid_timing].copy()
    frame = frame.dropna(subset=["glucose_lag_30m", "target_30m"]).reset_index(drop=True)
    return frame, resolved_source


def load_cgmacros_dataset(
    root: str | Path,
    *,
    glucose_source: str = "dexcom",
    horizon_minutes: int = 30,
) -> CGMacrosDataset:
    root_path = Path(root)
    files = discover_participant_files(root_path)
    if not files:
        raise FileNotFoundError(
            f"No CGMacros participant CSV files found below {root_path}. "
            "Run scripts/download_cgmacros.py first."
        )

    participant_ids = [_participant_id(path) for path in files]
    bio_rows = _bio_rows_by_participant(root_path, participant_ids)

    frames: list[pd.DataFrame] = []
    resolved_sources: set[str] = set()
    for path in files:
        participant_id = _participant_id(path)
        participant_frame, resolved_source = load_participant(
            path,
            bio_row=bio_rows.get(participant_id),
            glucose_source=glucose_source,
            horizon_minutes=horizon_minutes,
        )
        if not participant_frame.empty:
            frames.append(participant_frame)
            resolved_sources.add(resolved_source)

    if not frames:
        raise ValueError("CGMacros files were found but no usable forecasting rows could be created")

    frame = pd.concat(frames, ignore_index=True)
    features = [
        "glucose_mg_dl",
        "glucose_lag_15m",
        "glucose_lag_30m",
        "glucose_delta_15m",
        "sin_time",
        "cos_time",
        "carbs_last_120m",
        "protein_last_120m",
        "fat_last_120m",
        "fiber_last_120m",
        "heart_rate_mean_30m",
        "mets_mean_60m",
        "activity_calories_60m",
        "age",
        "bmi",
        "hba1c",
        "fasting_glucose",
        "fasting_insulin",
    ]
    source_label = next(iter(resolved_sources)) if len(resolved_sources) == 1 else "mixed"
    return CGMacrosDataset(
        frame=frame,
        feature_columns=features,
        target_column="target_30m",
        glucose_source=source_label,
        horizon_minutes=horizon_minutes,
    )


def save_preprocessed_dataset(dataset: CGMacrosDataset, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    dataset.frame.to_csv(output, index=False, compression="gzip")
    return output


def load_preprocessed_dataset(
    path: str | Path,
    *,
    glucose_source: str = "dexcom",
    horizon_minutes: int = 30,
) -> CGMacrosDataset:
    frame = pd.read_csv(
        path,
        parse_dates=["timestamp", "target_timestamp"],
        dtype={"participant_id": "string"},
        low_memory=False,
    )
    frame["participant_id"] = frame["participant_id"].astype(str).str.zfill(3)
    feature_columns = [
        "glucose_mg_dl",
        "glucose_lag_15m",
        "glucose_lag_30m",
        "glucose_delta_15m",
        "sin_time",
        "cos_time",
        "carbs_last_120m",
        "protein_last_120m",
        "fat_last_120m",
        "fiber_last_120m",
        "heart_rate_mean_30m",
        "mets_mean_60m",
        "activity_calories_60m",
        "age",
        "bmi",
        "hba1c",
        "fasting_glucose",
        "fasting_insulin",
    ]
    return CGMacrosDataset(
        frame=frame,
        feature_columns=feature_columns,
        target_column="target_30m",
        glucose_source=glucose_source,
        horizon_minutes=horizon_minutes,
    )
