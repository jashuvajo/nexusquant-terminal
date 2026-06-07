# AGENTS.md

## Cursor Cloud specific instructions

### Product overview

NexusQuant is a two-app repo: **FastAPI backend** (`backend/`) + **React/Vite frontend** (`frontend/`). There is no root npm/pnpm workspace. Docker Compose exists but is optional; Postgres/Redis fall back to in-memory when unavailable.

### System prerequisites

- **Node.js 22** and **Python 3.12** are required (matches `.github/workflows/ci.yml`).
- Ubuntu images need `python3.12-venv` before creating `backend/.venv` (`sudo apt-get install -y python3.12-venv`).
- Docker is optional for local dev; backend starts without Postgres/Redis using memory fallbacks.

### Starting services (manual)

**Backend** (port 8000):

```bash
cd backend
cp .env.example .env   # first time only; adjust CORS_ORIGINS for localhost:5173
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend** (port 5173):

```bash
cd frontend
cp .env.example .env   # first time only; set VITE_API_URL=http://localhost:8000
npm run dev -- --host 0.0.0.0 --port 5173
```

Use `VITE_STREAM_MODE=polling` locally (default in `.env.example`) for stable HTTP polling against the backend.

### Verify locally

- Backend: `curl http://localhost:8000/health` → `status: ok`
- Frontend: open `http://localhost:5173` — terminal UI loads; without Upstox credentials it shows the explicit setup/status panel (no dummy prices).

### Lint / build / tests

| Area | Command | Notes |
|------|---------|-------|
| Frontend lint | `cd frontend && npm run lint` | ESLint |
| Frontend build | `cd frontend && npm run build` | Typecheck + Vite build (CI) |
| Backend compile | `cd backend && source .venv/bin/activate && python -m compileall app` | CI check |
| Automated tests | none in repo | No pytest/jest suites currently |

### Upstox / live data

Real market data requires Upstox API credentials on the backend (`UPSTOX_API_KEY`, `UPSTOX_API_SECRET`, OAuth via `/api/upstox/login-url`). Without them, the app is still runnable for UI/API development; snapshots return explicit Upstox auth errors.

### Docker Compose (optional)

`docker compose up --build` starts backend + Postgres + Redis + Prometheus. The frontend is **not** in compose — run Vite separately or use Vercel for production builds.
