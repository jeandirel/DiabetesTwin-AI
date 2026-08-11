from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from diabetestwin.cgmacros import discover_participant_files


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(r"[^0-9eE+\-.]", "", regex=True),
        errors="coerce",
    )


def _parse_timestamp(series: pd.Series) -> pd.Series:
    # CGMacros combines sensor/activity feeds and may contain several textual datetime shapes.
    try:
        return pd.to_datetime(series, errors="coerce", format="mixed")
    except TypeError:
        return pd.to_datetime(series, errors="coerce")


def _near_future_count(
    frame: pd.DataFrame,
    minutes: int = 30,
    tolerance_minutes: float = 7.5,
) -> int:
    if frame.empty:
        return 0
    left = frame[["timestamp"]].copy()
    left["wanted"] = left["timestamp"] + pd.Timedelta(minutes=minutes)
    right = frame[["timestamp", "glucose"]].rename(
        columns={"timestamp": "matched_timestamp"}
    )
    left = left.sort_values("wanted")
    right = right.sort_values("matched_timestamp")
    merged = pd.merge_asof(
        left,
        right,
        left_on="wanted",
        right_on="matched_timestamp",
        direction="nearest",
        tolerance=pd.Timedelta(minutes=tolerance_minutes),
    )
    valid = merged["matched_timestamp"].notna() & (
        merged["matched_timestamp"] > merged["timestamp"]
    )
    return int(valid.sum())


def _sensor_frame(timestamp: pd.Series, glucose: pd.Series) -> pd.DataFrame:
    return (
        pd.DataFrame({"timestamp": timestamp, "glucose": glucose})
        .dropna()
        .drop_duplicates("timestamp")
        .sort_values("timestamp")
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("data/raw/cgmacros"))
    args = parser.parse_args()

    files = discover_participant_files(args.data_root)
    print(f"participant_files={len(files)}")
    totals = {
        "raw": 0,
        "parsed_timestamp": 0,
        "dexcom": 0,
        "libre": 0,
        "dexcom_near_30m": 0,
        "libre_near_30m": 0,
    }

    for index, path in enumerate(files):
        raw = pd.read_csv(path, low_memory=False)
        raw.columns = [str(column).lstrip("\ufeff").strip() for column in raw.columns]
        if index == 0:
            print("columns=" + repr(raw.columns.tolist()))
            examples = (
                raw.get("Timestamp", pd.Series(dtype=str))
                .dropna()
                .astype(str)
                .head(8)
                .tolist()
            )
            print("timestamp_examples=" + repr(examples))

        parsed = _parse_timestamp(raw["Timestamp"])
        dexcom = (
            _numeric(raw["Dexcom GL"])
            if "Dexcom GL" in raw.columns
            else pd.Series(np.nan, index=raw.index)
        )
        libre = (
            _numeric(raw["Libre GL"])
            if "Libre GL" in raw.columns
            else pd.Series(np.nan, index=raw.index)
        )

        dex = _sensor_frame(parsed, dexcom)
        lib = _sensor_frame(parsed, libre)

        dex_diff = dex["timestamp"].diff().dt.total_seconds().div(60).dropna()
        lib_diff = lib["timestamp"].diff().dt.total_seconds().div(60).dropna()
        dex_near = _near_future_count(dex)
        lib_near = _near_future_count(lib, tolerance_minutes=20.0)

        totals["raw"] += len(raw)
        totals["parsed_timestamp"] += int(parsed.notna().sum())
        totals["dexcom"] += len(dex)
        totals["libre"] += len(lib)
        totals["dexcom_near_30m"] += dex_near
        totals["libre_near_30m"] += lib_near

        pid = path.stem.split("-")[-1]
        print(
            f"{pid}: raw={len(raw)} parsed={parsed.notna().sum()} "
            f"dexcom={len(dex)} dex_med_gap={dex_diff.median() if not dex_diff.empty else np.nan:.2f} "
            f"dex_30m_pairs={dex_near} libre={len(lib)} "
            f"libre_med_gap={lib_diff.median() if not lib_diff.empty else np.nan:.2f} "
            f"libre_30m_pairs={lib_near}"
        )

    print("TOTALS=" + repr(totals))


if __name__ == "__main__":
    main()
