from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from starlette.responses import Response

from app.api.routes import router
from app.core.config import get_settings
from app.services.ai_engine import TradeQualityScorer
from app.services.market_simulator import MarketSimulator
from app.services.risk_engine import RiskEngine
from app.services.storage import AnalyticsStorage

settings = get_settings()
scorer = TradeQualityScorer()
risk_engine = RiskEngine(settings.ai_score_threshold, settings.safe_mode_threshold, settings.max_exposure_pct)
market = MarketSimulator(scorer, risk_engine)
storage = AnalyticsStorage(settings.database_url, settings.redis_url)

SNAPSHOTS_STREAMED = Counter("nexusquant_snapshots_streamed_total", "Market snapshots streamed to clients")
ACTIVE_WS = Gauge("nexusquant_active_websocket_clients", "Active WebSocket terminal clients")
LATEST_TQS = Gauge("nexusquant_latest_trade_quality_score", "Latest Trade Quality Score")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await storage.connect()
    yield
    await storage.close()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.websocket("/ws/market")
async def market_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    ACTIVE_WS.inc()
    try:
        while True:
            snapshot = market.next_snapshot()
            LATEST_TQS.set(snapshot["tradeQualityScore"])
            SNAPSHOTS_STREAMED.inc()
            await storage.persist_snapshot(snapshot)
            await websocket.send_json(snapshot)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    finally:
        ACTIVE_WS.dec()
