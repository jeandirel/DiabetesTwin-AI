from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diabetestwin.cgmacros import load_preprocessed_dataset
from diabetestwin.real_predictor import train_personalized_real_predictor


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark participant-specific chronological glucose forecasting on CGMacros."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/processed/cgmacros_forecasting.csv.gz"),
    )
    parser.add_argument("--model", choices=["hgb", "random_forest"], default="hgb")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()

    dataset = load_preprocessed_dataset(args.data)
    args.artifact_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for participant_id in dataset.participants:
        trained = train_personalized_real_predictor(
            dataset,
            participant_id,
            model_name=args.model,
            seed=args.seed,
        )
        evaluation = trained.evaluation
        participant = dataset.frame[
            dataset.frame["participant_id"].astype(str).str.zfill(3) == participant_id
        ]
        diagnosis = str(participant["diagnosis"].iloc[0]) if "diagnosis" in participant else "unknown"
        row = {
            "participant_id": participant_id,
            "diagnosis": diagnosis,
            **vars(evaluation),
            "mae_improvement_vs_persistence": round(
                evaluation.persistence_mae_mg_dl - evaluation.mae_mg_dl,
                2,
            ),
        }
        rows.append(row)
        print(
            f"{participant_id}: MAE={evaluation.mae_mg_dl:.2f} mg/dL, "
            f"persistence={evaluation.persistence_mae_mg_dl:.2f} mg/dL"
        )

    results = pd.DataFrame(rows).sort_values("participant_id").reset_index(drop=True)
    improvement = results["persistence_mae_mg_dl"] - results["mae_mg_dl"]
    summary = {
        "model_name": args.model,
        "participants": int(len(results)),
        "split_strategy": "within_patient_chronological_70_30",
        "mean_mae_mg_dl": round(float(results["mae_mg_dl"].mean()), 2),
        "median_mae_mg_dl": round(float(results["mae_mg_dl"].median()), 2),
        "mean_rmse_mg_dl": round(float(results["rmse_mg_dl"].mean()), 2),
        "median_rmse_mg_dl": round(float(results["rmse_mg_dl"].median()), 2),
        "mean_persistence_mae_mg_dl": round(float(results["persistence_mae_mg_dl"].mean()), 2),
        "median_persistence_mae_mg_dl": round(float(results["persistence_mae_mg_dl"].median()), 2),
        "mean_mae_improvement_vs_persistence": round(float(improvement.mean()), 2),
        "median_mae_improvement_vs_persistence": round(float(np.median(improvement)), 2),
        "participants_beating_persistence": int((improvement > 0).sum()),
        "participants_tying_persistence": int((improvement == 0).sum()),
        "source": "PhysioNet CGMacros v1.0.0",
        "doi": "10.13026/3z8q-x658",
        "license": "CC BY-NC-SA 4.0",
    }

    csv_path = args.artifact_dir / f"cgmacros_personalized_{args.model}_by_participant.csv"
    summary_path = args.artifact_dir / f"cgmacros_personalized_{args.model}_summary.json"
    results.to_csv(csv_path, index=False)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Saved per-participant results to {csv_path}")
    print(f"Saved summary to {summary_path}")


if __name__ == "__main__":
    main()
