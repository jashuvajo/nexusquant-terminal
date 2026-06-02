from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskDecision:
    safe_mode: bool
    allow_new_trade: bool
    reason: str
    max_exposure_pct: int
    ai_threshold: int
    size_multiplier: float


class RiskEngine:
    def __init__(self, normal_threshold: int = 76, safe_threshold: int = 86, max_exposure_pct: int = 42) -> None:
        self.normal_threshold = normal_threshold
        self.safe_threshold = safe_threshold
        self.max_exposure_pct = max_exposure_pct

    def evaluate(
        self,
        *,
        tqs: int,
        latency_ms: int,
        spread_quality: int,
        stale_data_ms: int,
        drawdown_pct: float,
        exposure_pct: int,
        disconnects: int,
    ) -> RiskDecision:
        safe_mode = any(
            [
                latency_ms > 140,
                spread_quality < 58,
                stale_data_ms > 1_500,
                drawdown_pct >= 2.4,
                exposure_pct >= self.max_exposure_pct,
                disconnects > 0,
            ]
        )
        threshold = self.safe_threshold if safe_mode else self.normal_threshold
        allow = tqs >= threshold and not (drawdown_pct >= 3.0 or stale_data_ms > 2_500)
        reason = "SAFE_MODE_GUARD" if safe_mode else "NORMAL_RISK_CLEAR"
        return RiskDecision(
            safe_mode=safe_mode,
            allow_new_trade=allow,
            reason=reason,
            max_exposure_pct=18 if safe_mode else self.max_exposure_pct,
            ai_threshold=threshold,
            size_multiplier=0.35 if safe_mode else 1.0,
        )
