# Nowhere — Phase-1 Updates (changelog)

This document records the scaffold and implementation work completed so far for the Phase-1 hybrid Nowhere app.

Summary
- Created a FastAPI monolith with thin HTTP handlers and application layer handlers.
- Implemented ephemeral Redis-backed repos for activities, joins, messages, presence, and GEO discovery.
- Implemented minimal Postgres repo for durable Venue storage and a Unit Of Work for grouped operations.
- Added HMAC-signed device token helpers for device-scoped anonymous attendees.
- Added `docker-compose.yml` with Redis, Postgres, API service and Caddy reverse proxy.
- Added docs: `architecture.md` and `redis-schema.md`.

Files added (high level)
- API entry: [backend/api/main.py](backend/api/main.py) — FastAPI app, startup/shutdown, health, thin endpoints.
- Config: [backend/config.py](backend/config.py) — environment-driven settings (Pydantic `Settings`).
- Application handlers: [backend/application/handlers.py](backend/application/handlers.py) — command/query handlers delegating to repositories.
- Domain models: [backend/domain/models.py](backend/domain/models.py) — `Activity`, `Attendee`, `Join`, `Message`, `Venue`, `OrganizerUser` (Pydantic).
- Redis infra: [backend/infrastructure/redis/repo.py](backend/infrastructure/redis/repo.py) — Redis repositories with TTL and GEO maintenance.
- Postgres infra: [backend/infrastructure/postgres/repo.py](backend/infrastructure/postgres/repo.py) — asyncpg pool and `PostgresVenueRepo`.
- Unit of Work: [backend/infrastructure/uow.py](backend/infrastructure/uow.py) — simple context manager coordinating Postgres transaction and Redis operations.
- Security: [backend/security/device_tokens.py](backend/security/device_tokens.py) — `sign_device_token()` / `verify_device_token()` using HMAC.
- Docker Compose: [docker-compose.yml](docker-compose.yml) — Redis, Postgres, API, Caddy reverse proxy (dev).
- Proxy config: [infra/proxy/Caddyfile](infra/proxy/Caddyfile) — reverse proxy to API.
- Docs: [docs/architecture.md](docs/architecture.md), [docs/redis-schema.md](docs/redis-schema.md)

Design notes
- Ephemeral state: all chat, joins, attendee presence, and activity discovery are stored in Redis with TTLs; lists and sets are TTL-managed to keep system lightweight.
- Durable state: venues and organizer users/events belong in Postgres (durable).
- Mobile path: stateless; device holds a signed token and interacts directly through FastAPI endpoints which only persist ephemeral data in Redis.
- GEO discovery: `GEOADD` and `GEOSEARCH` are used for location-based discovery. Activities with location metadata add a member to the `nowhere:activities:geo` index.
- UnitOfWork: coordinates Postgres transaction semantics with Redis writes. Cross-store atomicity is best-effort; consider compensating workers for stronger guarantees.

Sample Redis key patterns (Phase-1)
- `nowhere:activity:{activity_id}` -> serialized Activity (TTL)
- `nowhere:activities:geo` -> GEO index (GEOADD/GEOSEARCH)
- `nowhere:join:{join_id}` -> serialized Join (TTL)
- `nowhere:activity_attendees:{activity_id}` -> SET of attendee_ids (TTL)
- `nowhere:message:{message_id}` -> serialized Message (TTL)
- `nowhere:activity_messages:{activity_id}` -> LIST of Message objects (TTL)
- `nowhere:presence:{activity_id}:{attendee_id}` -> ephemeral presence key (short TTL)

Run locally (minimal)
1. Ensure Docker is running.
2. From repository root run:

```bash
docker-compose up --build
```

3. Health check: `http://localhost:8000/health`

Notes for maintainers
- Add Postgres migrations for `venues` table before running in production. The `PostgresVenueRepo` expects a `venues(id, name, metadata)` table; create a simple SQL migration.
- Add request/response Pydantic models for API endpoints and validate inputs.
- Add organizer authentication middleware (JWT/OAuth) for dashboard routes.

ASCII architecture diagram

Client Mobile (stateless device token)
  |
  v
 Caddy reverse proxy ---> FastAPI API (thin handlers)
                          |        \
                          |         +--> Postgres (durable: venues, organizer users, events)
                          +--> Redis (ephemeral: activities, joins, messages, GEO index)

Workers (optional Phase-2): subscribe to Redis / scan keys -> notifications, archiving, analytics

Next recommended steps (Phase-2 planning)
- Add a worker skeleton to consume Redis events and archive expired activities/messages to Postgres.
- Add migrations and a small `seeder.py` for Postgres venues.
- Implement tests for repositories and handlers; add CI job.
- Harden signed device tokens (rotate secrets, add kid/versioning) and add token issuance endpoint.

If you'd like, I can now:
- add a minimal Postgres migration SQL and `seeder.py`, or
- implement request/response Pydantic schemas and basic validation for the API endpoints.
