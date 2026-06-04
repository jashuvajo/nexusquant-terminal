from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.core.config import Settings
from app.services.ai_learning import ContinuousAILearner
from app.services.realtime_engine import as_float, as_int
from app.services.upstox_client import UpstoxClient


class HistoricalTrainer:
    def __init__(self, settings: Settings, client: UpstoxClient, learner: ContinuousAILearner) -> None:
        self.settings = settings
        self.client = client
        self.learner = learner

    async def train(
        self,
        symbol: str = "NIFTY",
        target_trades: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        interval: int = 1,
    ) -> dict[str, Any]:
        target = target_trades or self.settings.historical_training_target_trades
        instrument_key = self.settings.instrument_key_for(symbol)
        today = date.today()
        to_date = to_date or today.isoformat()
        from_date = from_date or (today - timedelta(days=180)).isoformat()
        candles: list[dict[str, Any]] = []
        samples: list[dict[str, Any]] = []
        chunks: list[dict[str, Any]] = []
        errors: list[str] = []
        for chunk_from, chunk_to in self._date_chunks(from_date, to_date, interval):
            try:
                payload = await self.client.historical_candles(instrument_key, "minutes", interval, chunk_to, chunk_from)
                chunk_candles = self._parse_candles(payload)
                chunk_samples = self._generate_scalp_samples(symbol, chunk_candles, max(0, target - len(samples)))
                candles.extend(chunk_candles)
                samples.extend(chunk_samples)
                chunks.append({"from": chunk_from, "to": chunk_to, "candles": len(chunk_candles), "samples": len(chunk_samples)})
                if len(samples) >= target:
                    break
            except Exception as exc:
                errors.append(f"{chunk_from}->{chunk_to}: {exc}")
                continue
        learning = await self.learner.train_from_historical_samples(samples)
        return {
            "symbol": symbol,
            "instrumentKey": instrument_key,
            "fromDate": from_date,
            "toDate": to_date,
            "chunks": chunks,
            "chunkErrors": errors[-10:],
            "candles": len(candles),
            "targetTrades": target,
            "generatedTrades": len(samples),
            "enoughSamples": len(samples) >= target,
            "learning": learning,
            "note": "Samples are generated from real Upstox historical candles using deterministic scalp rules; no fake market data is created.",
        }

    def _date_chunks(self, from_date: str, to_date: str, interval: int) -> list[tuple[str, str]]:
        start = date.fromisoformat(from_date)
        end = date.fromisoformat(to_date)
        if start > end:
            start, end = end, start
        max_days = 28 if interval <= 15 else 85
        chunks: list[tuple[str, str]] = []
        cursor = start
        while cursor <= end:
            chunk_end = min(end, cursor + timedelta(days=max_days))
            chunks.append((cursor.isoformat(), chunk_end.isoformat()))
            cursor = chunk_end + timedelta(days=1)
        return chunks

    def _parse_candles(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        raw = (payload.get("data") or {}).get("candles") or (payload.get("data") or {}).get("candle") or []
        parsed = []
        for candle in raw:
            if not isinstance(candle, list) or len(candle) < 6:
                continue
            parsed.append({
                "time": str(candle[0]),
                "open": as_float(candle[1]),
                "high": as_float(candle[2]),
                "low": as_float(candle[3]),
                "close": as_float(candle[4]),
                "volume": as_int(candle[5]),
            })
        return list(reversed(parsed))

    def _generate_scalp_samples(self, symbol: str, candles: list[dict[str, Any]], target: int) -> list[dict[str, Any]]:
        samples: list[dict[str, Any]] = []
        if len(candles) < 20:
            return samples
        for index in range(15, len(candles) - 6):
            window = candles[index - 10:index]
            current = candles[index]
            future = candles[index + 1:index + 7]
            high = max(candle["high"] for candle in window)
            low = min(candle["low"] for candle in window)
            avg_volume = sum(candle["volume"] for candle in window) / len(window) if window else 0
            atr = sum(abs(candle["high"] - candle["low"]) for candle in window) / len(window)
            previous_close = candles[index - 1]["close"]
            move = abs(current["close"] - previous_close)
            volume_confirmed = current["volume"] >= avg_volume * 1.15 if avg_volume else True
            breakout_strength = move / atr if atr else 0

            direction = None
            if current["close"] > high and breakout_strength >= 0.35:
                direction = "CALL"
            elif current["close"] < low and breakout_strength >= 0.35:
                direction = "PUT"
            if not direction or not volume_confirmed:
                continue

            entry = current["close"]
            target_points = max(5.0, atr * 0.8)
            initial_stop = max(2.0, min(3.0, atr * 0.55))
            trail_distance = max(1.0, atr * 0.35)
            partial_taken = False
            stop_price = entry - initial_stop if direction == "CALL" else entry + initial_stop
            best_favorable = entry
            exit_price = entry
            exit_reason = "time_stop"

            for candle in future:
                if direction == "CALL":
                    best_favorable = max(best_favorable, candle["high"])
                    if candle["low"] <= stop_price:
                        exit_price = stop_price
                        exit_reason = "fast_stop_or_delta_reversal"
                        break
                    if not partial_taken and candle["high"] >= entry + target_points:
                        partial_taken = True
                        stop_price = max(stop_price, entry + 0.25)
                    if partial_taken:
                        stop_price = max(stop_price, best_favorable - trail_distance)
                    exit_price = candle["close"]
                else:
                    best_favorable = min(best_favorable, candle["low"])
                    if candle["high"] >= stop_price:
                        exit_price = stop_price
                        exit_reason = "fast_stop_or_delta_reversal"
                        break
                    if not partial_taken and candle["low"] <= entry - target_points:
                        partial_taken = True
                        stop_price = min(stop_price, entry - 0.25)
                    if partial_taken:
                        stop_price = min(stop_price, best_favorable + trail_distance)
                    exit_price = candle["close"]

            if exit_reason == "time_stop" and partial_taken:
                exit_reason = "trailing_profit_lock"
            raw_pnl = (exit_price - entry) if direction == "CALL" else (entry - exit_price)
            # Conservative transaction cost/slippage estimate for scalping.
            pnl = raw_pnl - 0.35
            tqs = max(35, min(95, 58 + breakout_strength * 10 + (15 if volume_confirmed else 0) + (8 if partial_taken else 0)))
            if tqs < 64:
                continue
            regime = "TREND_EXPANSION" if volume_confirmed and partial_taken else "RANGE_ABSORPTION" if pnl >= 0 else "REVERSAL_RISK"
            samples.append({
                "symbol": symbol,
                "time": current["time"],
                "side": direction,
                "entry": round(entry, 2),
                "exit": round(exit_price, 2),
                "exitReason": exit_reason,
                "pnl": round(pnl, 2),
                "tqs": round(tqs),
                "volume": current["volume"],
                "atr": round(atr, 2),
                "regime": regime,
            })
            if len(samples) >= target:
                break
        return samples
