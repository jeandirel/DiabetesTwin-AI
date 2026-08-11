from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib

from diabetestwin.cgmacros import load_preprocessed_dataset
from diabetestwin.real_predictor import (
    compare_real_models,
    train_grouped_real_predictor,
    train_personalized_real_predictor,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train glucose forecasting models on preprocessed CGMacros data.")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/processed/cgmacros_forecasting.csv.gz"),
    )
    parser.add_argument("--model", choices=["hgb", "random_forest"], default="hgb")
    parser.add_argument("--split", choices=["grouped", "personalized"], default="grouped")
    parser.add_argument("--participant", type=str, default=None)
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()

    if not args.data.exists():
        raise FileNotFoundError(
            f"{args.data} does not exist. Run scripts/download_cgmacros.py and "
            "scripts/preprocess_cgmacros.py first."
        )

    dataset = load_preprocessed_dataset(args.data)
    args.artifact_dir.mkdir(parents=True, exist_ok=True)

    if args.compare:
        comparison = compare_real_models(
            dataset,
            split=args.split,
            participant_id=args.participant,
            seed=args.seed,
        )
        output = args.artifact_dir / f"cgmacros_{args.split}_comparison.csv"
        comparison.to_csv(output, index=False)
        print(comparison.to_string(index=False))
        print(f"Saved comparison to {output}")
        return

    if args.split == "grouped":
        trained = train_grouped_real_predictor(dataset, model_name=args.model, seed=args.seed)
        suffix = "grouped"
    else:
        if args.participant is None:
            raise ValueError("--participant is required when --split personalized")
        trained = train_personalized_real_predictor(
            dataset,
            args.participant.zfill(3),
            model_name=args.model,
            seed=args.seed,
        )
        suffix = f"participant_{args.participant.zfill(3)}"

    model_path = args.artifact_dir / f"cgmacros_{args.model}_{suffix}.joblib"
    metrics_path = args.artifact_dir / f"cgmacros_{args.model}_{suffix}_metrics.json"
    predictions_path = args.artifact_dir / f"cgmacros_{args.model}_{suffix}_predictions.csv"

    joblib.dump(trained.model, model_path)
    metrics = vars(trained.evaluation)
    metrics.update(
        {
            "source": "PhysioNet CGMacros v1.0.0",
            "doi": "10.13026/3z8q-x658",
            "license": "CC BY-NC-SA 4.0",
        }
    )
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    trained.predictions.to_csv(predictions_path, index=False)

    print(json.dumps(metrics, indent=2))
    print(f"Saved model to {model_path}")
    print(f"Saved predictions to {predictions_path}")


if __name__ == "__main__":
    main()
