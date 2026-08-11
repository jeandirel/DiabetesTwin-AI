from __future__ import annotations

from dataclasses import dataclass

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from .data import SyntheticDataset, make_synthetic_training_data
from .models import PatientProfile


@dataclass
class ModelEvaluation:
    mae_mg_dl: float
    rmse_mg_dl: float
    train_samples: int
    test_samples: int


@dataclass
class TrainedPredictor:
    model: HistGradientBoostingRegressor
    data: SyntheticDataset
    evaluation: ModelEvaluation

    def predict_row(self, row) -> float:
        x = row[self.data.feature_columns].to_frame().T
        return float(self.model.predict(x)[0])


def train_virtual_patient_predictor(
    patient: PatientProfile,
    *,
    days: int = 28,
    seed: int = 7,
) -> TrainedPredictor:
    """Train a 30-minute-ahead predictor on synthetic digital-twin trajectories.

    The split is temporal by day to avoid random leakage between adjacent CGM samples.
    """
    dataset = make_synthetic_training_data(patient, days=days, seed=seed)
    frame = dataset.frame
    split_day = max(1, int(frame["day"].max() * 0.78))
    train = frame[frame["day"] <= split_day]
    test = frame[frame["day"] > split_day]

    model = HistGradientBoostingRegressor(
        learning_rate=0.07,
        max_iter=220,
        max_leaf_nodes=31,
        l2_regularization=0.4,
        random_state=seed,
    )
    model.fit(train[dataset.feature_columns], train[dataset.target_column])
    predictions = model.predict(test[dataset.feature_columns])

    evaluation = ModelEvaluation(
        mae_mg_dl=round(float(mean_absolute_error(test[dataset.target_column], predictions)), 2),
        rmse_mg_dl=round(float(root_mean_squared_error(test[dataset.target_column], predictions)), 2),
        train_samples=int(len(train)),
        test_samples=int(len(test)),
    )
    return TrainedPredictor(model=model, data=dataset, evaluation=evaluation)


def prediction_interval(prediction: float, rmse: float, z: float = 1.64) -> tuple[float, float]:
    """Simple illustrative uncertainty band, not a calibrated clinical interval."""
    spread = max(5.0, z * rmse)
    return max(40.0, prediction - spread), min(400.0, prediction + spread)
