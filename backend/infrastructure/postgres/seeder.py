"""
Seeder for Phase-1 Postgres schema.

This script will:
- Connect to Postgres via asyncpg using the DSN from `backend.config.get_settings()`
- Insert 5 sample venues (UUIDs are deterministic in this script)
- Insert 2 sample organizer users (passwords hashed with bcrypt; no plain-text passwords are stored)
- Insert 10 sample events distributed across venues and organizer users

Usage:
  python backend/infrastructure/postgres/seeder.py

Requirements:
  - asyncpg
  - bcrypt (python-bcrypt) OR passlib

How it connects to the FastAPI repo:
  The script reads `POSTGRES_DSN` from `backend/config.py` so it uses the same connection string as the application.
"""
import asyncio
import asyncpg
import json
import random
import time
from datetime import datetime, timedelta, timezone
import uuid
import secrets

from backend.config import get_settings

try:
    import bcrypt
    def bcrypt_hash(pw_bytes: bytes) -> str:
        return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode()
except Exception:
    # fallback to passlib if bcrypt is not available
    try:
        from passlib.hash import bcrypt as passlib_bcrypt
        def bcrypt_hash(pw_bytes: bytes) -> str:
            # passlib expects text; base64 the bytes for a deterministic text to hash
            import base64
            text = base64.urlsafe_b64encode(pw_bytes).decode()
            return passlib_bcrypt.hash(text)
    except Exception:
        raise RuntimeError("bcrypt or passlib required for password hashing. Install 'bcrypt' or 'passlib'.")


SAMPLE_VENUE_IDS = [
    "11111111-1111-1111-1111-111111111111",
    "22222222-2222-2222-2222-222222222222",
    "33333333-3333-3333-3333-333333333333",
    "44444444-4444-4444-4444-444444444444",
    "55555555-5555-5555-5555-555555555555",
]

SAMPLE_ORG_IDS = [
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
]


async def wait_for_postgres(dsn: str, timeout: int = 30):
    start = time.time()
    while True:
        try:
            conn = await asyncpg.connect(dsn)
            await conn.close()
            return
        except Exception:
            if time.time() - start > timeout:
                raise
            await asyncio.sleep(1)


async def seed():
    settings = get_settings()
    dsn = settings.POSTGRES_DSN

    print("Waiting for Postgres to be available...")
    await wait_for_postgres(dsn)

    pool = await asyncpg.create_pool(dsn)

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Insert venues
            print("Inserting sample venues...")
            venues = []
            for i, vid in enumerate(SAMPLE_VENUE_IDS, start=1):
                venue = {
                    "id": vid,
                    "name": f"Sample Venue {i}",
                    "address": f"{100+i} Example St, City {i}",
                    "metadata": {"capacity_estimate": random.randint(50, 500), "location": {"lat": 37.7 + i * 0.01, "lon": -122.4 - i * 0.01}},
                }
                venues.append(venue)
                await conn.execute(
                    "INSERT INTO venues (id, name, address, metadata) VALUES ($1,$2,$3,$4) ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, address=EXCLUDED.address, metadata=EXCLUDED.metadata",
                    venue["id"], venue["name"], venue["address"], json.dumps(venue["metadata"]),
                )

            # Insert organizer users (bcrypt hash). We intentionally DO NOT persist any plaintext passwords.
            print("Inserting sample organizer users (passwords are hashed and not stored in plaintext)...")
            orgs = []
            for idx, oid in enumerate(SAMPLE_ORG_IDS, start=1):
                email = f"organizer{idx}@example.com"
                # generate secure random bytes as password material (no plaintext)
                pw_bytes = secrets.token_bytes(24)
                pw_hash = bcrypt_hash(pw_bytes)
                org = {"id": oid, "email": email, "password_hash": pw_hash}
                orgs.append(org)
                await conn.execute(
                    "INSERT INTO organizer_users (id, email, password_hash) VALUES ($1,$2,$3) ON CONFLICT (id) DO UPDATE SET email=EXCLUDED.email, password_hash=EXCLUDED.password_hash",
                    org["id"], org["email"], org["password_hash"],
                )

            # Insert events (10 events distributed across venues and organizers)
            print("Inserting sample events...")
            now = datetime.now(timezone.utc)
            for n in range(10):
                ev_id = str(uuid.uuid4())
                venue = random.choice(venues)
                created_by = random.choice(orgs)
                # Some events in future, some near-expiration
                start_offset_days = random.choice([0, 0, 1, 2, 5, 10, 30])
                start_time = now + timedelta(days=start_offset_days, hours=random.randint(0, 23))
                # expires_at: some events expire in 24 hours, others later
                if random.random() < 0.3:
                    expires_at = now + timedelta(hours=24)
                else:
                    expires_at = start_time + timedelta(hours=random.choice([2,4,6,24,48]))

                event = {
                    "id": ev_id,
                    "venue_id": venue["id"],
                    "title": f"Sample Event {n+1} @ {venue['name']}",
                    "description": f"This is a sample event number {n+1}.",
                    "start_time": start_time,
                    "expires_at": expires_at,
                    "capacity": random.choice([50, 100, 200, None]),
                    "created_by": created_by["id"],
                    "metadata": {"tags": ["music","social"] if n % 2 == 0 else ["meetup"]},
                }

                await conn.execute(
                    "INSERT INTO events (id, venue_id, title, description, start_time, expires_at, capacity, created_by, metadata) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) ON CONFLICT (id) DO NOTHING",
                    event["id"], event["venue_id"], event["title"], event["description"], event["start_time"], event["expires_at"], event["capacity"], event["created_by"], json.dumps(event["metadata"]),
                )

    await pool.close()
    print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())
