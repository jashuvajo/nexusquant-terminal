from __future__ import annotations

from typing import Any


class UpstoxClient:
    """Thin adapter boundary for Upstox MarketDataStreamerV3 and REST APIs.

    Production deployments should inject access tokens through the environment and
    replace the mock methods with signed Upstox SDK/API calls for market data,
    option chain, order placement, funds, positions, and order history.
    """

    def __init__(self, api_key: str | None = None, api_secret: str | None = None) -> None:
        self.api_key = api_key
        self.api_secret = api_secret

    async def health(self) -> dict[str, Any]:
        configured = bool(self.api_key and self.api_secret)
        return {
            "configured": configured,
            "streamer": "MarketDataStreamerV3",
            "brokerHealth": 98 if configured else 82,
            "mode": "live-ready" if configured else "mock-sandbox",
        }

    async def option_chain(self, symbol: str) -> dict[str, Any]:
        return {
            "symbol": symbol,
            "source": "upstox-option-chain-adapter",
            "bias": "CALL_BID_SUPPORT" if symbol.upper() == "NIFTY" else "PUT_WRITER_ABSORPTION",
            "gammaAlignment": 84,
        }

    async def portfolio(self) -> dict[str, Any]:
        return {
            "capital": 1_250_000,
            "margin": 348_000,
            "positions": 2,
            "orders": 14,
            "realizedPnl": 84_200,
            "unrealizedPnl": 9_200,
        }
