from __future__ import annotations

import argparse
import json
from pathlib import Path

from diabetestwin.cgmacros import load_cgmacros_dataset, save_preprocessed_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess CGMacros into a 30-minute glucose forecasting table.")
    parser.add_argument("--data-root", type=Path, default=Path("data/raw/cgmacros"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/cgmacros_forecasting.csv.gz"),
    )
    parser.add_argument("--glucose-source", choices=["dexcom", "libre", "auto"], default="dexcom")
    parser.add_argument("--horizon-minutes", type=int, default=30)
    args = parser.parse_args()

    dataset = load_cgmacros_dataset(
        args.data_root,
        glucose_source=args.glucose_source,
        horizon_minutes=args.horizon_minutes,
    )
    output = save_preprocessed_dataset(dataset, args.output)
    summary = {
        "rows": len(dataset.frame),
        "participants": len(dataset.participants),
        "participant_ids": dataset.participants,
        "glucose_source": dataset.glucose_source,
        "horizon_minutes": dataset.horizon_minutes,
        "features": dataset.feature_columns,
        "source": "PhysioNet CGMacros v1.0.0",
        "doi": "10.13026/3z8q-x658",
        "license": "CC BY-NC-SA 4.0",
    }
    summary_path = output.with_suffix(output.suffix + ".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Saved preprocessed data to {output}")


if __name__ == "__main__":
    main()
