from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline

from .cgmacros import CGMacrosDataset


@dataclass(frozen=True)
class RealModelEvaluation:
    model_name: str
    split_strategy: str
    mae_mg_dl: float
    rmse_mg_dl: float
    persistence_mae_mg_dl: float
    train_samples: int
    test_samples: int
    train_participants: int
    test_participants: int


@dataclass
class RealTrainedPredictor:
    model: Pipeline
    data: CGMacrosDataset
    evaluation: RealModelEvaluation
    predictions: pd.DataFrame


def _build_model(model_name: str, *, seed: int) -> object:
    normalized = model_name.lower().strip()
    if normalized in {"hgb", "hist_gradient_boosting", "histgradientboosting"}:
        return HistGradientBoostingRegressor(
            learning_rate=0.055,
            max_iter=300,
            max_leaf_nodes=31,
            l2_regularization=0.6,
            random_state=seed,
        )
    if normalized in {"rf", "random_forest", "randomforest"}:
        return RandomForestRegressor(
            n_estimators=240,
            min_samples_leaf=3,
            max_features=0.75,
            n_jobs=-1,
            random_state=seed,
        )
    raise ValueError("model_name must be one of: hgb, random_forest")


def _pipeline(dataset: CGMacrosDataset, model_name: str, *, seed: int) -> Pipeline:
    numeric = ColumnTransformer(
        [("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), dataset.feature_columns)],
        remainder="drop",
    )
    return Pipeline([("preprocess", numeric), ("model", _build_model(model_name, seed=seed))])


def _evaluation(
    dataset: CGMacrosDataset,
    test: pd.DataFrame,
    predictions: np.ndarray,
    *,
    model_name: str,
    split_strategy: str,
    train_samples: int,
    train_participants: int,
) -> RealModelEvaluation:
    target = test[dataset.target_column].to_numpy(dtype=float)
    persistence = test["glucose_mg_dl"].to_numpy(dtype=float)
    return RealModelEvaluation(
        model_name=model_name,
        split_strategy=split_strategy,
        mae_mg_dl=round(float(mean_absolute_error(target, predictions)), 2),
        rmse_mg_dl=round(float(root_mean_squared_error(target, predictions)), 2),
        persistence_mae_mg_dl=round(float(mean_absolute_error(target, persistence)), 2),
        train_samples=int(train_samples),
        test_samples=int(len(test)),
        train_participants=int(train_participants),
        test_participants=int(test["participant_id"].nunique()),
    )


def train_grouped_real_predictor(
    dataset: CGMacrosDataset,
    *,
    model_name: str = "hgb",
    test_size: float = 0.2,
    seed: int = 42,
) -> RealTrainedPredictor:
    """Train on real CGMacros with a participant-level holdout.

    Participant IDs are used as groups so the test set contains unseen people. This is a stricter
    estimate of cross-person generalization than a random row split and avoids leakage between nearby CGM points.
    """
    frame = dataset.frame.sort_values(["participant_id", "timestamp"]).reset_index(drop=True)
    if frame["participant_id"].nunique() < 3:
        raise ValueError("At least three participants are required for participant-level evaluation")

    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_index, test_index = next(
        splitter.split(frame, frame[dataset.target_column], groups=frame["participant_id"])
    )
    train = frame.iloc[train_index].copy()
    test = frame.iloc[test_index].copy()

    model = _pipeline(dataset, model_name, seed=seed)
    model.fit(train[dataset.feature_columns], train[dataset.target_column])
    predicted = model.predict(test[dataset.feature_columns])

    prediction_frame = test[["participant_id", "timestamp", "glucose_mg_dl", dataset.target_column]].copy()
    prediction_frame["prediction_30m"] = predicted
    prediction_frame = prediction_frame.sort_values(["participant_id", "timestamp"]).reset_index(drop=True)

    evaluation = _evaluation(
        dataset,
        test,
        predicted,
        model_name=model_name,
        split_strategy="participant_holdout",
        train_samples=len(train),
        train_participants=train["participant_id"].nunique(),
    )
    return RealTrainedPredictor(model=model, data=dataset, evaluation=evaluation, predictions=prediction_frame)


def train_personalized_real_predictor(
    dataset: CGMacrosDataset,
    participant_id: str,
    *,
    model_name: str = "hgb",
    train_fraction: float = 0.7,
    seed: int = 42,
) -> RealTrainedPredictor:
    """Train and evaluate a participant-specific 30-minute glucose predictor chronologically."""
    normalized_id = str(participant_id).zfill(3)
    participant_ids = dataset.frame["participant_id"].astype(str).str.zfill(3)
    participant = dataset.frame[participant_ids == normalized_id].copy()
    participant = participant.sort_values("timestamp").reset_index(drop=True)
    if len(participant) < 60:
        raise ValueError(f"Participant {normalized_id} does not have enough usable samples")

    split = int(len(participant) * train_fraction)
    split = min(max(split, 30), len(participant) - 20)
    train = participant.iloc[:split].copy()
    test = participant.iloc[split:].copy()

    model = _pipeline(dataset, model_name, seed=seed)
    model.fit(train[dataset.feature_columns], train[dataset.target_column])
    predicted = model.predict(test[dataset.feature_columns])

    prediction_frame = test[["participant_id", "timestamp", "glucose_mg_dl", dataset.target_column]].copy()
    prediction_frame["prediction_30m"] = predicted
    prediction_frame = prediction_frame.reset_index(drop=True)

    evaluation = _evaluation(
        dataset,
        test,
        predicted,
        model_name=model_name,
        split_strategy="within_patient_chronological",
        train_samples=len(train),
        train_participants=1,
    )
    return RealTrainedPredictor(model=model, data=dataset, evaluation=evaluation, predictions=prediction_frame)


def compare_real_models(
    dataset: CGMacrosDataset,
    *,
    split: str = "grouped",
    participant_id: str | None = None,
    seed: int = 42,
) -> pd.DataFrame:
    rows = []
    for model_name in ["hgb", "random_forest"]:
        if split == "grouped":
            trained = train_grouped_real_predictor(dataset, model_name=model_name, seed=seed)
        elif split == "personalized":
            if participant_id is None:
                raise ValueError("participant_id is required for personalized comparison")
            trained = train_personalized_real_predictor(
                dataset,
                participant_id,
                model_name=model_name,
                seed=seed,
            )
        else:
            raise ValueError("split must be grouped or personalized")
        rows.append(vars(trained.evaluation))
    return pd.DataFrame(rows).sort_values("mae_mg_dl").reset_index(drop=True)
