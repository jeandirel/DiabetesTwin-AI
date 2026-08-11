from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib

from diabetestwin.models import PatientProfile
from diabetestwin.predictor import train_virtual_patient_predictor


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the DiabetesTwin-AI synthetic 30-minute predictor")
    parser.add_argument("--phenotype", choices=["balanced", "insulin_resistant", "active"], default="balanced")
    parser.add_argument("--days", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("artifacts/predictor.joblib"))
    args = parser.parse_args()

    patient = PatientProfile.from_phenotype(args.phenotype)
    trained = train_virtual_patient_predictor(patient, days=args.days)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": trained.model,
            "feature_columns": trained.data.feature_columns,
            "phenotype": args.phenotype,
            "evaluation": trained.evaluation.__dict__,
        },
        args.output,
    )
    print(json.dumps(trained.evaluation.__dict__, indent=2))
    print(f"Saved model to {args.output}")


if __name__ == "__main__":
    main()
