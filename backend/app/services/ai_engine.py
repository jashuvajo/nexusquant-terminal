from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:  # XGBoost is optional until a trained model artifact is mounted in production.
    import xgboost as xgb  # type: ignore
except Exception:  # pragma: no cover - dependency may not be installed in local smoke tests.
    xgb = None


@dataclass(frozen=True)
class EngineWeight:
    name: str
    weight: float


ENGINE_WEIGHTS = [
    EngineWeight("Delta Engine", 0.16),
    EngineWeight("Momentum Engine", 0.14),
    EngineWeight("Heatmap Engine", 0.12),
    EngineWeight("Volume Engine", 0.10),
    EngineWeight("Regime Engine", 0.10),
    EngineWeight("Spread Analysis", 0.09),
    EngineWeight("Option Chain Bias", 0.10),
    EngineWeight("Gamma Positioning", 0.10),
    EngineWeight("IV Expansion", 0.05),
    EngineWeight("Market Profile Alignment", 0.04),
]


class TradeQualityScorer:
    """Deterministic scoring adapter with a slot for a trained XGBoost model."""

    def __init__(self) -> None:
        self.model: Any | None = None
        if xgb is not None:
            self.model = None

    def score(self, features: dict[str, float]) -> tuple[int, list[dict[str, Any]]]:
        matrix: list[dict[str, Any]] = []
        for index, engine in enumerate(ENGINE_WEIGHTS):
            feature_key = engine.name.lower().replace(" ", "_")
            raw_value = features.get(feature_key, features.get("baseline", 72.0))
            adjusted = max(0, min(99, raw_value + (index % 3) * 2.5))
            matrix.append(
                {
                    "engine": engine.name,
                    "score": round(adjusted),
                    "weight": engine.weight,
                    "status": "pass" if adjusted >= 78 else "watch" if adjusted >= 62 else "fail",
                }
            )
        tqs = round(sum(item["score"] * item["weight"] for item in matrix))
        return tqs, matrix
