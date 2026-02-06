import pytest
import asyncpg


@pytest.mark.asyncio
async def test_postgres_simple(postgres_container):
    """Start a Postgres container and run a simple create/insert/select

    The `postgres_container` fixture yields a DSN for connecting with asyncpg.
    """
    # Connect directly with asyncpg to the test container
    conn = await asyncpg.connect(postgres_container)
    try:
        await conn.execute("CREATE TABLE IF NOT EXISTS test_tbl (id serial PRIMARY KEY, name text);")
        await conn.execute("INSERT INTO test_tbl(name) VALUES($1)", "alice")
        row = await conn.fetchrow("SELECT name FROM test_tbl WHERE id=1")
        assert row["name"] == "alice"
    finally:
        await conn.execute("DROP TABLE IF EXISTS test_tbl;")
        await conn.close()
