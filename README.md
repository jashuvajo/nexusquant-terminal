# NexusQuant Institutional Terminal

NexusQuant is a deployable institutional-style AI scalping terminal scaffold for Indian index options on NIFTY and SENSEX.

## Stack

- Frontend: React, TypeScript, Vite, TailwindCSS, Lightweight Charts, Recharts, Framer Motion, WebSocket client
- Backend: FastAPI, asyncio, WebSockets, Redis boundary, PostgreSQL boundary, XGBoost-ready AI scoring, Prometheus metrics, Docker
- Deployment: Vercel frontend, Render backend, PostgreSQL, Redis, Prometheus/Grafana-ready metrics, GitHub Actions CI

## Modules

The terminal includes Execution HUD, Heatmap Terminal, Orderflow Analytics, AI Matrix, Greeks & IV, Strategy Router, Upstox Portfolio, Risk Engine, Infrastructure Telemetry, AI Analytics, Trade Journal, Session Intelligence, Backtesting, and Settings.

## Local frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend connects to `VITE_WS_URL`. If the backend is unavailable, it automatically runs a local simulated one-second market stream.

## Local backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Useful endpoints:

- `GET /health`
- `GET /metrics`
- `GET /api/terminal/state`
- `GET /api/upstox/health`
- `WS /ws/market`

## Docker Compose

```bash
docker compose up --build
```

Services:

- Frontend: run separately with Vite or deploy to Vercel
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Prometheus: `http://localhost:9090`

## Vercel

Use the repository root. `vercel.json` builds `frontend` and serves `frontend/dist`.

Set environment variables:

```text
VITE_API_URL=https://nexusquant-api.onrender.com
VITE_WS_URL=wss://nexusquant-api.onrender.com/ws/market
```

## Render

`render.yaml` defines the FastAPI Docker service plus PostgreSQL and Redis. Configure secrets in Render:

```text
CORS_ORIGINS=https://your-vercel-domain.vercel.app
UPSTOX_API_KEY=...
UPSTOX_API_SECRET=...
```

## Production integration notes

The Upstox adapter is intentionally isolated in `backend/app/services/upstox_client.py`. Replace the mock methods with MarketDataStreamerV3, option chain APIs, order APIs, funds APIs, and positions APIs once broker credentials and order permissions are available.

The execution pipeline is represented as:

1. Infrastructure telemetry and failsafe validation
2. Session intelligence and regime classification
3. Heatmap and liquidity sweep analysis
4. Multi-engine AI scoring
5. Option chain, Greeks, and gamma confirmation
6. Adaptive sizing and smart routing
7. Execution quality monitoring
8. Adaptive trailing engine
9. AI learning and analytics storage

This scaffold does not place live orders by default. Keep execution disabled until broker credentials, exchange approvals, audit logging, and risk limits are validated.
