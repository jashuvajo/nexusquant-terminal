from __future__ import annotations

import json
from typing import Any

try:
    import asyncpg  # type: ignore
except Exception:  # pragma: no cover
    asyncpg = None

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None


class AnalyticsStorage:
    """Persistence boundary for ticks, AI scores, greeks, heatmaps and executions."""

    def __init__(self, database_url: str, redis_url: str) -> None:
        self.database_url = database_url
        self.redis_url = redis_url
        self._pool: Any | None = None
        self._redis: Any | None = None

    async def connect(self) -> None:
        if asyncpg is not None:
            try:
                self._pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=4)
            except Exception:
                self._pool = None
        if redis is not None:
            try:
                self._redis = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
        if self._redis is not None:
            await self._redis.aclose()

    async def persist_snapshot(self, snapshot: dict[str, Any]) -> None:
        if self._redis is not None:
            await self._redis.set("nexusquant:last_snapshot", json.dumps(snapshot), ex=30)
        if self._pool is not None:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    create table if not exists market_snapshots (
                        id bigserial primary key,
                        created_at timestamptz default now(),
                        symbol text not null,
                        tqs integer not null,
                        payload jsonb not null
                    )
                    """
                )
                await conn.execute(
                    "insert into market_snapshots(symbol, tqs, payload) values($1, $2, $3::jsonb)",
                    snapshot["symbol"],
                    snapshot["tradeQualityScore"],
                    json.dumps(snapshot),
                )
