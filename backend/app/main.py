from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from starlette.responses import Response

from app.api.routes import alias_router, router
from app.core.config import get_settings
from app.services.ai_engine import TradeQualityScorer
from app.services.realtime_engine import MarketConfigurationError, RealTimeMarketEngine
from app.services.risk_engine import RiskEngine
from app.services.storage import AnalyticsStorage
from app.services.trading_control import TradingControl
from app.services.upstox_auth import UpstoxAuthService
from app.services.upstox_client import UpstoxAuthRequired, UpstoxClient, UpstoxDataError

settings = get_settings()
scorer = TradeQualityScorer()
risk_engine = RiskEngine(settings.ai_score_threshold, settings.safe_mode_threshold, settings.max_exposure_pct)
auth_service = UpstoxAuthService(
    api_key=settings.upstox_api_key,
    api_secret=settings.upstox_api_secret,
    redirect_uri=settings.upstox_redirect_uri,
    redis_url=settings.redis_url,
    access_token=settings.upstox_access_token,
)
upstox_client = UpstoxClient(settings.upstox_api_key, settings.upstox_api_secret, auth_service)
trading_control = TradingControl(settings.redis_url)
market_engine = RealTimeMarketEngine(settings, upstox_client, scorer, risk_engine, trading_control)
storage = AnalyticsStorage(settings.database_url, settings.redis_url)

SNAPSHOTS_STREAMED = Counter("nexusquant_snapshots_streamed_total", "Real Upstox market snapshots streamed to clients")
STREAM_ERRORS = Counter("nexusquant_stream_errors_total", "Market stream status/error messages sent to clients")
ACTIVE_WS = Gauge("nexusquant_active_websocket_clients", "Active WebSocket terminal clients")
LATEST_TQS = Gauge("nexusquant_latest_trade_quality_score", "Latest Trade Quality Score")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await storage.connect()
    yield
    await storage.close()


app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(alias_router)


@app.get("/health")
async def health() -> dict[str, str | bool]:
    token_status = await auth_service.token_status()
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
        "upstoxConfigured": token_status["configured"],
        "upstoxTokenPresent": token_status["hasToken"],
    }


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def stream_status(websocket: WebSocket, status: str, message: str) -> None:
    STREAM_ERRORS.inc()
    await websocket.send_json({"type": "status", "status": status, "message": message})


@app.websocket("/ws/market")
async def market_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    ACTIVE_WS.inc()
    try:
        while True:
            try:
                snapshot = await market_engine.snapshot()
                LATEST_TQS.set(snapshot["tradeQualityScore"])
                SNAPSHOTS_STREAMED.inc()
                await storage.persist_snapshot(snapshot)
                await websocket.send_json(snapshot)
            except UpstoxAuthRequired as exc:
                await stream_status(websocket, "UPSTOX_AUTH_REQUIRED", str(exc))
            except MarketConfigurationError as exc:
                await stream_status(websocket, "CONFIGURATION_REQUIRED", str(exc))
            except UpstoxDataError as exc:
                await stream_status(websocket, "UPSTOX_DATA_ERROR", str(exc))
            except Exception as exc:
                await stream_status(websocket, "STREAM_ERROR", f"Unexpected stream error: {exc}")
            await asyncio.sleep(settings.market_poll_seconds)
    except WebSocketDisconnect:
        pass
    finally:
        ACTIVE_WS.dec()
