"""Fitted model state. available_information_cutoff is mandatory."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.learning.definition import Algorithm
from quantlab.learning.pca import FittedPCA
from quantlab.learning.scale import FittedScaler
from quantlab.learning.trees import FittedTree


class FitArtifact(BaseModel):
    algorithm: Algorithm
    intercept: float = 0.0
    coefficients: list[float] = Field(default_factory=list)
    feature_names: list[str] = Field(default_factory=list)
    scaler: FittedScaler | None = None
    pca: FittedPCA | None = None
    selected: list[str] = Field(default_factory=list)
    trees: list[FittedTree] = Field(default_factory=list)
    learning_rate: float | None = None
    init_pred: float | None = None
    train_mean: float | None = None
    condition_number: float | None = None
    train_rmse: float | None = None
    n_train: int = 0


class ModelState(BaseModel):
    schema_version: str = "1"
    model_definition_id: str
    fit_timestamp: datetime
    training_start: datetime | None = None
    training_end: datetime | None = None
    available_information_cutoff: datetime
    artifact: FitArtifact | None = None
    feature_schema: list[str] = Field(default_factory=list)
    training_sample_count: int = 0
    random_seed: int = 0
    software_version: str = "1.1.0"
    data_snapshot: str = ""
    config_hash: str = ""
    note: str = "What could this model know when it was fitted?"


class ModelPrediction(BaseModel):
    model_state_id: str
    instrument: str
    prediction_time: datetime
    prediction: float
    n_train: int = 0
    regime: str | None = None
    note: str = "frozen before outcome realization"
