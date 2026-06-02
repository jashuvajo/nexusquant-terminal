from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.services.upstox_client import UpstoxClient

router = APIRouter(prefix="/api", tags=["terminal"])


def get_upstox(settings: Settings = Depends(get_settings)) -> UpstoxClient:
    return UpstoxClient(settings.upstox_api_key, settings.upstox_api_secret)


@router.get("/terminal/state")
async def terminal_state() -> dict[str, str]:
    return {
        "pipeline": "telemetry -> regime -> heatmap -> ai-score -> greeks -> routing -> trailing -> analytics",
        "symbols": "NIFTY,SENSEX",
        "mode": "semi-automated-scalping-infrastructure",
    }


@router.get("/upstox/health")
async def upstox_health(client: UpstoxClient = Depends(get_upstox)) -> dict:
    return await client.health()


@router.get("/upstox/portfolio")
async def upstox_portfolio(client: UpstoxClient = Depends(get_upstox)) -> dict:
    return await client.portfolio()


@router.get("/upstox/option-chain/{symbol}")
async def option_chain(symbol: str, client: UpstoxClient = Depends(get_upstox)) -> dict:
    return await client.option_chain(symbol)


@router.get("/risk/config")
async def risk_config(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "aiScoreThreshold": settings.ai_score_threshold,
        "safeModeThreshold": settings.safe_mode_threshold,
        "maxExposurePct": settings.max_exposure_pct,
        "dailyDrawdownPct": settings.daily_drawdown_pct,
    }
