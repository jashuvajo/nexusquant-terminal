from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from app.services.ai_engine import TradeQualityScorer
from app.services.risk_engine import RiskEngine

REGIMES = ["TREND_EXPANSION", "RANGE_ABSORPTION", "VOLATILITY_COMPRESSION", "REVERSAL_RISK"]
VOL_REGIMES = ["NORMAL_IV", "IV_EXPANSION", "LOW_IV", "EVENT_SPIKE"]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def wave(tick: int, speed: float, phase: float = 0) -> float:
    return math.sin(tick / speed + phase)


class MarketSimulator:
    def __init__(self, scorer: TradeQualityScorer, risk_engine: RiskEngine) -> None:
        self.scorer = scorer
        self.risk_engine = risk_engine
        self.tick = 0

    def next_snapshot(self) -> dict[str, Any]:
        self.tick += 1
        tick = self.tick
        symbol = "NIFTY" if tick % 7 < 4 else "SENSEX"
        spot_base = 23650 if symbol == "NIFTY" else 78120
        step = 50 if symbol == "NIFTY" else 100
        spot = round(spot_base + wave(tick, 9) * 86 + wave(tick, 2.7) * 18, 2)
        atm = round(spot / step) * step

        features = {
            "baseline": 72 + wave(tick, 4.8) * 16,
            "delta_engine": 70 + wave(tick, 2.2) * 24,
            "momentum_engine": 72 + wave(tick, 3.4) * 22,
            "heatmap_engine": 74 + wave(tick, 4.1) * 18,
            "volume_engine": 68 + wave(tick, 3.0) * 24,
            "regime_engine": 75 + wave(tick, 6.2) * 16,
            "spread_analysis": 86 + wave(tick, 5.0) * 10,
            "option_chain_bias": 73 + wave(tick, 4.4) * 22,
            "gamma_positioning": 76 + wave(tick, 5.7) * 18,
            "iv_expansion": 64 + wave(tick, 2.8) * 30,
            "market_profile_alignment": 70 + wave(tick, 6.5) * 20,
        }
        tqs, ai_matrix = self.scorer.score(features)

        spread_quality = round(clamp(84 + wave(tick, 3.7) * 13, 22, 99))
        latency = round(clamp(38 + abs(wave(tick, 4.9)) * 24, 8, 130))
        stale_data = round(clamp(120 + abs(wave(tick, 5)) * 420, 40, 1800))
        drawdown = round(clamp(0.7 + abs(wave(tick, 10)) * 1.2, 0, 4.5), 2)
        exposure = round(clamp(21 + wave(tick, 5) * 14, 5, 48))
        disconnects = 1 if tqs < 68 and tick % 5 == 0 else 0
        risk_decision = self.risk_engine.evaluate(
            tqs=tqs,
            latency_ms=latency,
            spread_quality=spread_quality,
            stale_data_ms=stale_data,
            drawdown_pct=drawdown,
            exposure_pct=exposure,
            disconnects=disconnects,
        )

        heatmap = [
            {
                "id": f"{symbol}-{index}",
                "strike": atm + (index - 8) * step,
                "side": "FUTURE" if index % 3 == 0 else "CALL" if index % 2 == 0 else "PUT",
                "liquidity": round(clamp(54 + wave(tick + index, 3.4) * 35 + (8 - abs(index - 8)) * 3, 12, 99)),
                "absorption": round(clamp(44 + wave(tick, 4.1, index * 0.7) * 38, 3, 99)),
                "gammaWall": round(clamp(40 + abs(index - 8) * 4 + wave(tick, 7, index) * 26, 4, 98)),
                "stopDensity": round(clamp(35 + wave(tick, 4.5, index - 8) * 30 + (18 if abs(index - 8) > 5 else 0), 5, 96)),
                "sweepRisk": round(clamp(28 + wave(tick, 2.8, index) * 42, 2, 94)),
                "label": "Liquidity cluster" if index in (7, 8, 9) else "Gamma wall" if index in (4, 13) else "Acceptance",
            }
            for index in range(18)
        ]

        telemetry = [
            {
                "time": f"{(9 + index // 6) % 24:02d}:{(index * 5) % 60:02d}",
                "pnl": round(wave(tick - 35 + index, 6) * 4200 + index * 120 - 1700),
                "tqs": round(clamp(72 + wave(tick - 35 + index, 4) * 18, 30, 98)),
                "latency": round(clamp(31 + wave(tick - 35 + index, 3, 1.2) * 18, 8, 98)),
                "volume": round(clamp(4200 + wave(tick - 35 + index, 3.8) * 2500 + index * 90, 900, 11000)),
                "price": round(spot + wave(tick - 35 + index, 8) * 34 + index * 1.7, 2),
            }
            for index in range(36)
        ]

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "spot": spot,
            "atmStrike": atm,
            "premiumFocusZone": f"{atm - step}-{atm + step} {symbol} weekly options",
            "aiConfidence": round(clamp(tqs + wave(tick, 4.2) * 7, 10, 99)),
            "tradeQualityScore": tqs,
            "pnl": round(12800 + wave(tick, 6) * 9400),
            "liveExposurePct": exposure,
            "spreadQuality": spread_quality,
            "executionLatencyMs": latency,
            "deltaVelocity": round(clamp(62 + wave(tick, 2.8) * 36, -100, 100)),
            "trailingStopState": "SAFE MODE - reduced size" if risk_decision.safe_mode else "Adaptive target extension" if tqs > 82 else "ATR trail armed",
            "regime": REGIMES[abs(tick // 6) % len(REGIMES)],
            "volatilityRegime": VOL_REGIMES[abs(tick // 8) % len(VOL_REGIMES)],
            "activeTrades": [
                {
                    "id": "NQ-ALPHA-01",
                    "symbol": symbol,
                    "side": "CALL" if wave(tick, 5) > 0 else "PUT",
                    "strike": atm,
                    "qty": 75 if risk_decision.safe_mode else 150,
                    "entry": round(142 + wave(tick, 9) * 12, 2),
                    "ltp": round(154 + wave(tick, 3.4) * 18, 2),
                    "pnl": round(6200 + wave(tick, 4) * 4800),
                    "tqs": tqs,
                    "stop": round(126 + wave(tick, 5) * 4, 2),
                    "target": round(188 + wave(tick, 6) * 12, 2),
                    "status": "SAFE_MODE" if risk_decision.safe_mode else "TRAILING" if tqs > 85 else "SCALPING",
                }
            ],
            "heatmap": heatmap,
            "orderflow": {
                "cumulativeDelta": round(42000 + wave(tick, 5) * 36000),
                "deltaVelocity": round(clamp(58 + wave(tick, 2.2) * 44, -100, 100)),
                "aggressiveBuyers": round(clamp(71 + wave(tick, 3.1) * 25, 5, 99)),
                "aggressiveSellers": round(clamp(37 + wave(tick, 4.3) * 24, 3, 99)),
                "domImbalance": round(clamp(56 + wave(tick, 2.9) * 37, -100, 100)),
                "liquidityShift": round(clamp(64 + wave(tick, 5.2) * 22, 0, 99)),
                "sweepDetection": round(clamp(48 + wave(tick, 3.6) * 39, 0, 99)),
                "volumeAcceleration": round(clamp(68 + wave(tick, 4.5) * 28, 0, 99)),
                "breakoutVelocity": round(clamp(61 + wave(tick, 3.8) * 33, 0, 99)),
            },
            "greeks": {
                "delta": round(0.54 + wave(tick, 6) * 0.18, 2),
                "gamma": round(0.018 + abs(wave(tick, 4)) * 0.022, 3),
                "theta": round(-4.2 - abs(wave(tick, 7)) * 2.4, 2),
                "vega": round(9.6 + wave(tick, 5) * 2.2, 2),
                "ivRank": round(clamp(54 + wave(tick, 8) * 31, 1, 99)),
                "ivPercentile": round(clamp(62 + wave(tick, 9) * 24, 1, 99)),
                "ivExpansion": round(clamp(39 + wave(tick, 2.7) * 42, 0, 99)),
            },
            "marketProfile": {
                "poc": atm - step,
                "vah": atm + step * 2,
                "val": atm - step * 3,
                "acceptanceZone": "Breakout accepted above VAH" if tqs > 78 else "Auction inside value area",
                "volumeProfile": [
                    {"level": atm + (index - 6) * step, "volume": round(clamp(1200 + wave(tick, 3.3, index) * 900 + (6 - abs(index - 6)) * 260, 120, 4200))}
                    for index in range(12)
                ],
            },
            "aiMatrix": ai_matrix,
            "risk": {
                "safeMode": risk_decision.safe_mode,
                "dailyDrawdownPct": drawdown,
                "maxDrawdownPct": 3,
                "slippageBps": round(clamp(3.2 + abs(wave(tick, 4)) * 4.5, 1, 18), 1),
                "staleDataMs": stale_data,
                "apiDisconnects": disconnects,
                "latencyMs": latency,
                "spreadWideningPct": round(clamp(3 + abs(wave(tick, 3.1)) * 9, 0, 22), 1),
                "maxExposurePct": risk_decision.max_exposure_pct,
                "cooldownSeconds": 180 if risk_decision.safe_mode else 25,
            },
            "infra": {
                "brokerHealth": 82 if disconnects else 98,
                "websocketLatencyMs": round(clamp(18 + abs(wave(tick, 3.6)) * 23, 5, 120)),
                "orderRouterLatencyMs": round(clamp(24 + abs(wave(tick, 3.9)) * 34, 8, 150)),
                "redisHealth": 99,
                "postgresHealth": 98,
                "prometheusHealth": 99,
            },
            "portfolio": {
                "capital": 1_250_000,
                "margin": 348_000,
                "realizedPnl": 84_200,
                "unrealizedPnl": round(9_200 + wave(tick, 4) * 6_200),
                "executionQuality": round(clamp(88 + wave(tick, 5.4) * 8, 55, 99)),
                "positions": 2,
                "orders": 14,
            },
            "strategy": {
                "selected": "Capital preservation scalp" if risk_decision.safe_mode else "Momentum expansion scalp" if tqs > 84 else "Liquidity acceptance scalp",
                "aggression": 26 if risk_decision.safe_mode else round(clamp(58 + wave(tick, 4.2) * 28, 10, 92)),
                "sizeMultiplier": risk_decision.size_multiplier,
                "threshold": risk_decision.ai_threshold,
                "router": "SAFE_MODE" if risk_decision.safe_mode else "AGGRESSIVE_SWEEP" if tqs > 87 else "SMART_LIMIT" if tqs > 76 else "PASSIVE_JOIN",
            },
            "telemetry": telemetry,
            "journal": [
                {
                    "time": f"{10 + index:02d}:{(tick * 3 + index * 7) % 60:02d}",
                    "instrument": "NIFTY 50 CE" if index % 2 == 0 else "SENSEX PE",
                    "tqs": round(clamp(68 + wave(tick, 3, index) * 21, 45, 98)),
                    "pnl": round(2400 + wave(tick, 4, index) * 6200),
                    "exitReason": ["ATR trail lock", "Gamma wall rejection", "Partial exit plus runner", "Safe mode flatten", "Breakout velocity fade"][index % 5],
                }
                for index in range(6)
            ],
            "backtest": [
                {"name": "Win Rate", "value": 68.4, "unit": "%"},
                {"name": "Profit Factor", "value": 2.18, "unit": "x"},
                {"name": "Avg Hold", "value": 4.6, "unit": "min"},
                {"name": "Max DD", "value": 1.9, "unit": "%"},
                {"name": "Sharpe", "value": 3.4, "unit": ""},
                {"name": "Expectancy", "value": 1280, "unit": "INR"},
            ],
            "executionDecision": {
                "allowNewTrade": risk_decision.allow_new_trade,
                "reason": risk_decision.reason,
            },
        }
