from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.services.ai_engine import TradeQualityScorer
from app.services.realtime_engine import MarketConfigurationError, RealTimeMarketEngine
from app.services.risk_engine import RiskEngine
from app.services.session import current_session_state
from app.services.upstox_auth import UpstoxAuthError, UpstoxAuthService
from app.services.upstox_client import UpstoxAuthRequired, UpstoxClient, UpstoxDataError

router = APIRouter(prefix="/api", tags=["terminal"])


class ScalpOrderRequest(BaseModel):
    instrument_token: str = Field(..., description="Upstox instrument key for the selected option contract")
    quantity: int = Field(..., gt=0)
    transaction_type: Literal["BUY", "SELL"] = "BUY"
    order_type: Literal["LIMIT", "MARKET"] = "LIMIT"
    price: float = Field(..., ge=0)
    market_protection: int = Field(0, ge=0, le=100)
    tag: str = "nexusquant-scalp"


def get_upstox_auth(settings: Settings = Depends(get_settings)) -> UpstoxAuthService:
    return UpstoxAuthService(
        api_key=settings.upstox_api_key,
        api_secret=settings.upstox_api_secret,
        redirect_uri=settings.upstox_redirect_uri,
        redis_url=settings.redis_url,
    )


def get_upstox(
    settings: Settings = Depends(get_settings),
    auth_service: UpstoxAuthService = Depends(get_upstox_auth),
) -> UpstoxClient:
    return UpstoxClient(settings.upstox_api_key, settings.upstox_api_secret, auth_service)


def get_market_engine(
    settings: Settings = Depends(get_settings),
    client: UpstoxClient = Depends(get_upstox),
) -> RealTimeMarketEngine:
    scorer = TradeQualityScorer()
    risk_engine = RiskEngine(settings.ai_score_threshold, settings.safe_mode_threshold, settings.max_exposure_pct)
    return RealTimeMarketEngine(settings, client, scorer, risk_engine)


@router.get("/terminal/state")
async def terminal_state(settings: Settings = Depends(get_settings)) -> dict[str, str | bool | float | None]:
    return {
        "pipeline": "Upstox token -> option chain -> market quote -> intraday candles -> risk gates -> execution router",
        "symbols": "NIFTY,SENSEX",
        "mode": "real-upstox-data-only",
        "primarySymbol": settings.primary_symbol,
        "niftyExpiryDate": settings.nifty_expiry_date,
        "sensexExpiryDate": settings.sensex_expiry_date,
        "liveTradingEnabled": settings.enable_live_trading,
        "aggressiveMode": settings.aggressive_mode,
        "marketPollSeconds": settings.market_poll_seconds,
    }


@router.get("/market/snapshot/{symbol}")
async def market_snapshot(symbol: Literal["NIFTY", "SENSEX"], engine: RealTimeMarketEngine = Depends(get_market_engine)) -> dict:
    try:
        return await engine.snapshot(symbol)
    except (UpstoxAuthRequired, UpstoxDataError, MarketConfigurationError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/upstox/login-url")
async def upstox_login_url(auth_service: UpstoxAuthService = Depends(get_upstox_auth)) -> dict[str, str]:
    try:
        return {"loginUrl": auth_service.login_url()}
    except UpstoxAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/upstox/callback")
async def upstox_callback(
    code: str = Query(..., description="Authorization code returned by Upstox"),
    auth_service: UpstoxAuthService = Depends(get_upstox_auth),
) -> dict:
    try:
        token_meta = await auth_service.exchange_code(code)
    except UpstoxAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "message": "Upstox access token stored successfully. You can close this tab and return to NexusQuant.",
        **token_meta,
    }


@router.get("/upstox/token/status")
async def upstox_token_status(auth_service: UpstoxAuthService = Depends(get_upstox_auth)) -> dict:
    return await auth_service.token_status()


@router.get("/upstox/health")
async def upstox_health(client: UpstoxClient = Depends(get_upstox)) -> dict:
    return await client.health()


@router.get("/upstox/portfolio")
async def upstox_portfolio(client: UpstoxClient = Depends(get_upstox)) -> dict:
    try:
        return {"funds": await client.funds(), "positions": await client.positions(), "orders": await client.orders()}
    except (UpstoxAuthRequired, UpstoxDataError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/upstox/option-chain/{symbol}")
async def option_chain(symbol: Literal["NIFTY", "SENSEX"], settings: Settings = Depends(get_settings), client: UpstoxClient = Depends(get_upstox)) -> dict:
    expiry = settings.expiry_for(symbol)
    if not expiry:
        raise HTTPException(status_code=400, detail=f"{symbol}_EXPIRY_DATE is not configured.")
    try:
        return await client.option_chain(settings.instrument_key_for(symbol), expiry)
    except (UpstoxAuthRequired, UpstoxDataError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/execution/scalp-order")
async def place_scalp_order(
    request: ScalpOrderRequest,
    settings: Settings = Depends(get_settings),
    client: UpstoxClient = Depends(get_upstox),
) -> dict:
    session = current_session_state()
    if not settings.enable_live_trading:
        raise HTTPException(status_code=403, detail="Live trading is disabled. Set ENABLE_LIVE_TRADING=true only after paper checks and risk approval.")
    if not session.execution_allowed:
        raise HTTPException(status_code=403, detail=f"Execution blocked: {session.label}. {session.reason}")
    if request.order_type == "MARKET" and request.market_protection <= 0:
        raise HTTPException(status_code=400, detail="Aggressive MARKET orders require market_protection > 0.")

    order = {
        "quantity": request.quantity,
        "product": "I",
        "validity": "IOC" if settings.aggressive_mode else "DAY",
        "price": request.price if request.order_type == "LIMIT" else 0,
        "tag": request.tag,
        "instrument_token": request.instrument_token,
        "order_type": request.order_type,
        "transaction_type": request.transaction_type,
        "disclosed_quantity": 0,
        "trigger_price": 0,
        "is_amo": False,
        "market_protection": request.market_protection,
    }
    try:
        response = await client.place_order(order)
    except (UpstoxAuthRequired, UpstoxDataError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"submitted": True, "session": session.label, "order": order, "upstox": response}


@router.get("/risk/config")
async def risk_config(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "aiScoreThreshold": settings.ai_score_threshold,
        "safeModeThreshold": settings.safe_mode_threshold,
        "maxExposurePct": settings.max_exposure_pct,
        "dailyDrawdownPct": settings.daily_drawdown_pct,
        "enableLiveTrading": settings.enable_live_trading,
        "aggressiveMode": settings.aggressive_mode,
    }
