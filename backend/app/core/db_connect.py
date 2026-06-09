from __future__ import annotations


def asyncpg_connect_kwargs(database_url: str) -> dict[str, str]:
    """Return asyncpg connection kwargs for managed Postgres endpoints."""
    if "rds.amazonaws.com" in database_url:
        return {"ssl": "require"}
    return {}
