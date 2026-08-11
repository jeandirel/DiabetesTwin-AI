from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

DIAGNOSES = ("healthy", "prediabetes", "type2_diabetes")
SOURCE = "PhysioNet CGMacros v1.0.0"
DOI = "10.13026/3z8q-x658"
LICENSE = "CC BY-NC-SA 4.0"


def select_demo_subset(frame: pd.DataFrame, *, hours: int = 48) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    data = frame.copy()
    data["participant_id"] = data["participant_id"].astype(str).str.zfill(3)
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")
    data["target_timestamp"] = pd.to_datetime(data["target_timestamp"], errors="coerce")
    data = data.dropna(subset=["timestamp"]).sort_values(["participant_id", "timestamp"])

    selected_frames: list[pd.DataFrame] = []
    participants: list[dict[str, object]] = []

    for diagnosis in DIAGNOSES:
        diagnosis_frame = data[data["diagnosis"].astype(str) == diagnosis]
        if diagnosis_frame.empty:
            raise ValueError(f"No participant found for diagnosis group: {diagnosis}")

        chosen: pd.DataFrame | None = None
        chosen_id = ""
        for participant_id in sorted(diagnosis_frame["participant_id"].unique().tolist()):
            participant = diagnosis_frame[diagnosis_frame["participant_id"] == participant_id].sort_values("timestamp")
            if participant.empty:
                continue
            start = participant["timestamp"].iloc[0]
            window = participant[participant["timestamp"] < start + pd.Timedelta(hours=hours)].copy()
            if len(window) >= 600:
                chosen = window
                chosen_id = participant_id
                break

        if chosen is None:
            raise ValueError(f"No sufficiently long participant timeline found for diagnosis group: {diagnosis}")

        selected_frames.append(chosen)
        participants.append(
            {
                "participant_id": chosen_id,
                "diagnosis": diagnosis,
                "rows": int(len(chosen)),
                "start": chosen["timestamp"].min().isoformat(),
                "end": chosen["timestamp"].max().isoformat(),
            }
        )

    demo = pd.concat(selected_frames, ignore_index=True).sort_values(["participant_id", "timestamp"])
    return demo, participants


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a small licensed CGMacros demo subset for deployment demos.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/cgmacros_forecasting.csv.gz"),
        help="Full preprocessed CGMacros forecasting table.",
    )
    parser.add_argument("--output", type=Path, default=Path("data/demo/cgmacros_demo.csv"))
    parser.add_argument("--hours", type=int, default=48)
    args = parser.parse_args()

    if args.hours < 12:
        raise ValueError("Demo window must be at least 12 hours")

    frame = pd.read_csv(
        args.input,
        dtype={"participant_id": "string"},
        parse_dates=["timestamp", "target_timestamp"],
        low_memory=False,
    )
    demo, participants = select_demo_subset(frame, hours=args.hours)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    demo.to_csv(args.output, index=False)

    metadata = {
        "source": SOURCE,
        "doi": DOI,
        "license": LICENSE,
        "purpose": "Non-clinical deployment/demo subset",
        "selection": (
            "One released participant per HbA1c-derived dataset group; "
            "earliest 48-hour usable window by default."
        ),
        "rows": int(len(demo)),
        "participants": participants,
        "privacy": "Timestamps remain privacy-shifted exactly as released by CGMacros.",
    }
    metadata_path = args.output.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(metadata, indent=2))
    print(f"Saved demo CSV to {args.output}")
    print(f"Saved metadata to {metadata_path}")


if __name__ == "__main__":
    main()
