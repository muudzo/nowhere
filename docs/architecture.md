# Nowhere - Phase-1 Architecture

Overview
- FastAPI monolith provides HTTP API for both mobile consumers and organizer dashboard.
- Ephemeral state (activities, joins, messages, presence) lives in Redis with TTLs.
- Durable state for organizers, venues and event metadata lives in Postgres.
- Caddy (reverse proxy) sits in front for TLS, routing, and static file hosting.

Key boundaries
- Mobile consumer path: stateless HTTP calls, uses device-scoped signed tokens, only touches Redis for ephemeral operations.
- Organizer path: authenticated users manage venues/events stored in Postgres.
- Background workers (Phase-2): optional consumers that read Redis streams or keys to send notifications, archive to Postgres, or compute analytics.

Data flow (high level)
1. Mobile app requests a device token (signed) — no durable user created.
2. Mobile creates or discovers an activity; ephemeral Activity stored in Redis (TTL).
3. Attendees join: join record saved to Redis plus attendee set on activity.
4. Messages posted to activity: saved to Redis list; presence maintained via ephemeral keys.
5. Organizers create venues/events: stored in Postgres; venue location is used to maintain GEO indexes in Redis for fast discovery.

Extension points (Phase-2)
- Workers consuming Redis streams to deliver push notifications and to materialize historical archives to Postgres.
- Analytics worker aggregating joins/messages into time-series DB.
- Optional auth provider or SSO for organizer users.
