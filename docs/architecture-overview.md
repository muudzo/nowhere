**Architecture Overview**
- **Project:** nowhere — FastAPI backend, Postgres, Redis, Caddy proxy, mobile/web frontends.
- **Compose file:** [docker-compose.yml](docker-compose.yml)

**Services**
- **API (backend):** Python/FastAPI app in [backend/](backend) served by Uvicorn: entrypoint `backend.api.main` ([backend/api/main.py](backend/api/main.py)).
- **Postgres:** `postgres:15` (configured in `docker-compose.yml`).
- **Redis:** `redis:7` used for caching and geo/index features.
- **Proxy:** Caddy (`caddy:2`) configured by [infra/proxy/Caddyfile](infra/proxy/Caddyfile).

**Directory layout (key folders/files)**
- **backend/**: main backend package with modules and application logic.
  - [backend/api/main.py](backend/api/main.py): FastAPI app and routes (includes `/health`).
  - [backend/config.py](backend/config.py): Settings (now using `pydantic-settings`).
  - [backend/Dockerfile](backend/Dockerfile): image build for API (uses Python 3.13.4).
  - [backend/requirements.txt](backend/requirements.txt): Python dependencies (includes `pydantic-settings`).
  - [backend/infrastructure/redis/repo.py](backend/infrastructure/redis/repo.py): Redis client (now uses `redis.asyncio`).
- **docs/**: documentation files (this file).
- **check_stack.sh**: stack verification script at repository root.
- **docker-compose.yml**: multi-service orchestration; build config for `api` points to `backend/Dockerfile`.

**Recent changes applied (quick summary)**
- Migrated `BaseSettings` usage to `pydantic-settings` (`backend/config.py`).
- Replaced `aioredis` with `redis.asyncio` in `backend/infrastructure/redis/repo.py`.
- Updated `backend/Dockerfile` to ensure `/app/backend` is copied and to use `python:3.13.4-slim`.
- Updated `docker-compose.yml` to build with repository root context and run `uvicorn backend.api.main:app`.
- Added `check_stack.sh` with robust checks for API, Postgres, Redis, and Caddy.

**Current status (as of latest run)**
- Containers: API, Postgres, Redis, and Caddy start via `docker-compose up -d`.
- Health endpoint (`/health`) returns HTTP 200 when API successfully started.
- `check_stack.sh` reports Postgres and Redis connectivity; proxy routing validated.

**Known warnings / issues**
- `docker-compose.yml` contains a top-level `version: '3.8'` and Docker logs show a deprecation warning: Docker CLI ignores `version` attribute in Compose v2 — consider removing it to silence warnings.
- Dependency compatibility: FastAPI + Pydantic v2 require `pydantic-settings` for `BaseSettings` (already migrated). Confirm other modules do not import `BaseSettings` from `pydantic`.
- Confirm all runtime dependencies are present in `backend/requirements.txt` (e.g. `redis` vs `redis.asyncio` usage is compatible with `redis==5.0.1`; we switched code to `redis.asyncio` but dependency is `redis` package — ensure correct package/version for target python).
- Ensure tests and CI run in Python 3.13.4; local `pyenv` has been configured for the developer environment.

**Areas to inspect next (prioritized)**
- Verify `backend/requirements.txt` pins a `redis` package version compatible with the `redis.asyncio` API (or explicitly `redis>=4.x` as needed).
- Audit repository for any remaining `from pydantic import BaseSettings` imports and replace with `from pydantic_settings import BaseSettings`.
- Add simple CI job to build the Docker images and run `check_stack.sh` in CI (or an integration stage).
- Confirm database migrations are applied (look at `migrations/` and `backend/infrastructure/postgres/repo.py` seeding logic).
- Add smoke/integration tests for `/health`, Postgres connectivity, and Redis ping.

**Quick developer commands**
```bash
# ensure correct pyenv version
pyenv shell 3.13.4

# build and start stack
docker-compose up -d --build

# run verification
./check_stack.sh

# view API logs
docker-compose logs --tail=200 api
```

**Next steps I can take (pick any)**
- Update `backend/requirements.txt` to pin a compatible `redis` package/version or add `aioredis` back if preferred.
- Run a repo-wide search and replace for `BaseSettings` import locations and fix them.
- Add a CI workflow that runs the build and `check_stack.sh`.

If you want, I will also open a checklist PR with the remaining fixes and CI additions.
