# Nowhere - Architecture & Improvement Points

## System Architecture

```
                    +------------------+
                    |   React Native   |
                    |   (Expo / TS)    |
                    +--------+---------+
                             |
                     HTTPS/REST + WS
                             |
                    +--------+---------+
                    |   Caddy Proxy    |
                    | (IP rate limiting)|
                    +--------+---------+
                             |
                    +--------+---------+
                    |  FastAPI (async) |
                    |  Python 3.13     |
                    +--------+---------+
                             |
                    +--------+---------+
                    |      Redis 7     |
                    | (primary store + |
                    |  event stream)   |
                    +------------------+
                    |   PostgreSQL 15  |
                    |  (optional, off  |
                    |   by default)    |
                    +------------------+
```

## Backend Architecture (Domain-Driven Design)

The backend follows a layered DDD + CQRS approach:

```
API Layer (api/)
  ├── intents.py          FastAPI route handlers
  ├── auth.py             JWT handshake
  ├── ws.py               WebSocket endpoint + ConnectionManager
  ├── metrics.py          /metrics operational endpoint
  ├── schemas.py          Pydantic models (with input validation & sanitization)
  ├── message_schemas.py  Message schemas (with HTML sanitization)
  ├── deps.py             Dependency injection
  └── limiter.py          Per-user rate limiting

Service Layer (services/)
  ├── intent_command_handler.py   Write path (commands)
  ├── intent_query_service.py     Read path (queries)
  ├── ranking_service.py          Configurable intent ranking
  ├── clustering_service.py       Zoom-aware geo clustering
  └── metrics_event_handler.py    Async event consumers

Domain Layer (core/)
  ├── models/intent.py    Aggregate root + value objects
  ├── models/ranking.py   Score calculation (configurable weights)
  ├── commands.py         Command definitions
  ├── events.py           Domain events
  ├── event_bus.py        Pub/sub dispatch (with optional event store)
  ├── unit_of_work.py     Transaction protocol
  ├── logging.py          Structured JSON logging + correlation IDs
  └── clock.py            Time abstraction (testable)

Infrastructure Layer (infra/)
  └── persistence/
      ├── intent_repo.py  Geo-indexed intent storage (data access only)
      ├── join_repo.py    Atomic join operations (Lua)
      ├── message_repo.py Ephemeral message lists
      ├── event_store.py  Redis Stream event persistence
      ├── metrics_repo.py Counter-based metrics
      ├── unit_of_work.py Redis pipeline transactions
      ├── keys.py         Redis key schema
      └── lua_scripts.py  Atomic Redis operations
```

### Key Patterns

- **CQRS**: Commands (create, join, message) separated from queries (nearby, clusters)
- **Unit of Work**: Redis pipeline wraps all writes in a single atomic transaction; domain events collected and published after commit
- **Domain Events**: `IntentCreated`, `IntentJoined`, `MessagePosted`, `IntentFlagged` -- persisted to Redis Stream, then dispatched to handlers
- **Event Persistence**: All domain events written to `nowhere:events` Redis Stream (capped at 10k entries) before handler dispatch, enabling replay and auditing
- **Geo-Spatial Indexing**: Redis `GEOADD`/`GEOSEARCH` for proximity queries
- **Lua Scripts**: Atomic join operations (check-then-write) to prevent race conditions
- **Configurable Ranking**: `score = W_DIST * dist + W_FRESH * fresh + W_POP * pop` -- weights configurable via env vars (`RANKING_W_DIST`, `RANKING_W_FRESH`, `RANKING_W_POP`)
- **WebSocket + Polling Fallback**: Real-time message delivery via WebSocket (`/ws/intents/{id}/messages`) with automatic 3s polling fallback
- **Structured Logging**: JSON-formatted logs with request-scoped correlation IDs (`request_id` context var) propagated through all log entries
- **Input Validation**: Coordinate bounds (-90/90, -180/180), HTML sanitization on all user text, radius capping

### Frontend Architecture

```
App.tsx (react-navigation NativeStackNavigator)
  ├── HomeScreen        FlatList of nearby intents
  ├── CreateScreen      Intent creation form (modal presentation)
  └── ChatScreen        WebSocket real-time + polling fallback

hooks/
  ├── useIntents.ts        Orchestrator (location + fetch + join)
  ├── useLocation.ts       Permission + coordinate fetching
  ├── useNearbyIntents.ts  API data fetching (retains stale data on error)
  └── useJoinIntent.ts     Join action

utils/
  ├── config.ts         Env-based API URL (NOWHERE_API_URL / platform defaults)
  ├── api.ts            Axios instance + JWT interceptor + error interceptor
  ├── identity.ts       Device UUID + token management
  ├── location.ts       expo-location wrapper
  └── network.ts        useNetworkStatus hook (online/offline detection)

i18n/
  ├── index.ts          t() function with {{interpolation}} support
  └── en.ts             English string catalog
```

### Authentication Flow

```
Device boots → generate UUID → store in SecureStore
  → POST /auth/handshake { anon_id } → receive JWT
  → attach JWT to all requests via axios interceptor
  → rotate identity every 30 days
```

No email, no password, no registration. Fully anonymous, device-scoped.

### Redis Data Model

| Key Pattern | Type | Purpose |
|---|---|---|
| `intent:{id}` | Hash | Intent data (title, emoji, lat, lon, etc.) |
| `intents:geo` | Sorted Set (Geo) | Geospatial index for proximity search |
| `intent:{id}:joins` | Set | User IDs who joined |
| `intent:{id}:messages` | List | Capped at 100 messages |
| `intent:{id}:flags` | Set | User IDs who flagged |
| `user:{id}:intents` | Set | Intents created by user |
| `ratelimit:{action}:{user_id}` | String (counter) | Rate limit tracking |
| `nowhere:events` | Stream | Persisted domain events (capped at 10k) |
| `nowhere:counter:{name}` | String (counter) | Operational metrics counters |

All intent-related keys have TTL = 24 hours (matching ephemeral lifecycle).

---

## Improvement Points -- Resolution Log

All 15 improvements identified in the initial assessment have been implemented:

### Critical -- RESOLVED

| # | Issue | Resolution | Commit |
|---|-------|------------|--------|
| 1 | Hardcoded LAN IP (`10.10.0.69`) | Extracted to `config.ts` with env var (`NOWHERE_API_URL`), platform-aware dev defaults, and prod fallback | `6ef57bd` |
| 2 | No CI/CD pipeline | GitHub Actions with parallel jobs: backend tests (Redis service), linting (ruff), frontend typecheck, Docker build, stack integration | `f8fb9d7` |

### High Priority -- RESOLVED

| # | Issue | Resolution | Commit |
|---|-------|------------|--------|
| 3 | Polling-based chat (3s interval) | WebSocket endpoint (`/ws/intents/{id}/messages`) with ConnectionManager broadcast; frontend auto-falls back to polling on WS failure | `a316f18` |
| 4 | `useState` screen routing | `@react-navigation/native-stack` with typed `RootStackParamList`; modal presentation for Create; navigation props replace callbacks | `8933851` |
| 5 | Raw error alerts, no offline state | Axios response interceptor with `userMessage`; `useNetworkStatus` hook; stale data retention on fetch failure | `8471d81` |

### Medium Priority -- RESOLVED

| # | Issue | Resolution | Commit |
|---|-------|------------|--------|
| 6 | Fire-and-forget events | `RedisEventStore` persists to `nowhere:events` Stream (capped 10k) before handler dispatch; `read_since()` for replay | `326f292` |
| 7 | Magic ranking weights in repo | `RankingService` with env-configurable weights (`RANKING_W_DIST/FRESH/POP`); extracted from repository | `20f77e2` |
| 8 | Repository does ranking + clustering | `ClusteringService` extracted; repo returns raw `(intent, distance)` pairs and `get_geo_points()` | `5adab85` |
| 9 | Integration tests skipped | Fixed with `httpx.ASGITransport`; removed all `@pytest.mark.skip`; tests exercise full request lifecycle | `b0afc34` |
| 10 | No structured logging/metrics | `request_id` context var in all JSON logs; `/metrics` endpoint with Redis counters + event stream stats; client X-Request-ID passthrough | `4ef7baf` |
| 11 | No input validation/sanitization | `field_validator` on schemas: coordinate bounds, HTML escape, length caps; IP rate limiting in Caddyfile; radius/limit capping on nearby endpoint | `0eee534` |

### Low Priority -- RESOLVED

| # | Issue | Resolution | Commit |
|---|-------|------------|--------|
| 12 | PostgreSQL running idle | `POSTGRES_ENABLED` flag (default: false); DB init skipped when disabled; documented as optional analytics layer | `2e9ef72` |
| 13 | Fixed-precision clustering | `ClusteringService` accepts `?zoom=` param mapped to precision (1-4 decimals); falls back to radius-based precision | `221d2c4` |
| 14 | No accessibility support | `accessibilityLabel` and `accessibilityHint` on all interactive elements across all screens; intent cards announce full context | `82b52fd` |
| 15 | Hardcoded English strings | `i18n/` module with `t()` function, `{{interpolation}}`, English catalog covering all screens and errors | `ea6aa0c` |

---

## Remaining Opportunities (Future Work)

These are not blockers but would further improve the system:

- **E2E tests**: Add Detox/Maestro for mobile E2E testing
- **OpenTelemetry**: Full distributed tracing (currently only correlation IDs)
- **Redis Cluster**: High availability for production at scale
- **CSRF tokens**: For web clients making state-changing requests
- **Consumer groups**: Redis Stream consumer groups for reliable event processing with retry
- **Client-side clustering**: Use `supercluster` for smoother map interactions
- **Push notifications**: Notify users when someone joins their intent
- **WCAG AA audit**: Contrast ratios and focus management beyond basic labels

---

## Architecture Decision Records

| Decision | Rationale |
|---|---|
| Redis as primary store | Ephemeral data (24hr TTL) fits Redis naturally. Geo-indexing built-in. Sub-ms reads. |
| Redis Streams for events | Avoids adding a separate event store (Kafka, EventStoreDB). Events are ephemeral like the data. |
| Anonymous identity | Removes signup friction. Aligns with "no social graph" philosophy. |
| CQRS with event persistence | Commands and queries separated. Events persisted for auditing but not used as source of truth (not full event sourcing). |
| WebSocket + polling fallback | Real-time UX when possible, graceful degradation on unreliable connections. |
| PostgreSQL optional | Redis handles all primary needs. Postgres available for analytics if needed, but not required. |
| Rate limiting at two layers | Per-user in application (fine-grained), per-IP in Caddy (DDoS protection). |
| Caddy as reverse proxy | Automatic HTTPS, simple config, IP rate limiting. Suitable for single-server deployment. |
| react-navigation | Standard Expo-compatible navigation. Deep linking, gestures, screen lifecycle. |
| Expo for mobile | Cross-platform with minimal native code. Fast iteration for MVP. |
| i18n foundation early | String extraction is cheaper now than after more screens are added. |
