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
        if len(candles) < 8:
            return samples
        for index in range(5, len(candles) - 3):
            window = candles[index - 5:index]
            current = candles[index]
            future = candles[index + 1:index + 4]
            high = max(candle["high"] for candle in window)
            low = min(candle["low"] for candle in window)
            avg_volume = sum(candle["volume"] for candle in window) / len(window) if window else 0
            direction = None
            if current["close"] > high:
                direction = "CALL"
            elif current["close"] < low:
                direction = "PUT"
            if not direction:
                continue
            entry = current["close"]
            if direction == "CALL":
                best = max(candle["high"] for candle in future)
                worst = min(candle["low"] for candle in future)
                pnl = min(5.0, best - entry) if best - entry >= 5 else min(best - entry, worst - entry)
            else:
                best = min(candle["low"] for candle in future)
                worst = max(candle["high"] for candle in future)
                pnl = min(5.0, entry - best) if entry - best >= 5 else min(entry - best, entry - worst)
            volume_confirmed = current["volume"] >= avg_volume if avg_volume else False
            move = abs(current["close"] - candles[index - 1]["close"])
            tqs = max(35, min(95, 55 + move * 2 + (15 if volume_confirmed else 0)))
            regime = "TREND_EXPANSION" if volume_confirmed and pnl > 0 else "RANGE_ABSORPTION" if pnl >= 0 else "REVERSAL_RISK"
            samples.append({
                "symbol": symbol,
                "time": current["time"],
                "side": direction,
                "entry": entry,
                "pnl": round(pnl, 2),
                "tqs": round(tqs),
                "volume": current["volume"],
                "regime": regime,
            })
            if len(samples) >= target:
                break
        return samples
