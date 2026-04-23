import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

_db_path: Path = Path.home() / ".garmin_mcp_cache.db"
_SHORT_TTL = timedelta(hours=1)
_STATIC_TTL = timedelta(hours=4)


@contextmanager
def _connect():
    conn = sqlite3.connect(_db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS activity_details (
            activity_id TEXT PRIMARY KEY,
            data        TEXT NOT NULL,
            fetched_at  TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS activity_list (
            cache_key  TEXT PRIMARY KEY,
            data       TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_data (
            cache_key  TEXT PRIMARY KEY,
            data       TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS static_data (
            cache_key  TEXT PRIMARY KEY,
            data       TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        )
    """)
    conn.commit()
    try:
        yield conn
    finally:
        conn.close()


def _cache_get(table: str, cache_key: str, ttl: timedelta | None) -> dict | list | None:
    try:
        with _connect() as conn:
            row = conn.execute(
                f"SELECT data, fetched_at FROM {table} WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
            if not row:
                return None
            if ttl is not None and datetime.now(UTC) - datetime.fromisoformat(row[1]) > ttl:
                return None
            return json.loads(row[0])
    except Exception:
        logger.warning("Cache read failed for %s key=%s", table, cache_key)
        return None


def _cache_set(table: str, cache_key: str, data: dict | list) -> None:
    try:
        with _connect() as conn:
            conn.execute(
                f"INSERT OR REPLACE INTO {table} VALUES (?, ?, ?)",
                (cache_key, json.dumps(data), datetime.now(UTC).isoformat()),
            )
            conn.commit()
    except Exception:
        logger.warning("Cache write failed for %s key=%s", table, cache_key)


def get_activity_details(activity_id: str) -> dict | None:
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT data, fetched_at FROM activity_details WHERE activity_id = ?",
                (str(activity_id),),
            ).fetchone()
            if not row:
                return None
            return json.loads(row[0])
    except Exception:
        logger.warning("Cache read failed for activity_id=%s", activity_id)
        return None


def set_activity_details(activity_id: str, data: dict) -> None:
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO activity_details VALUES (?, ?, ?)",
                (str(activity_id), json.dumps(data), datetime.now(UTC).isoformat()),
            )
            conn.commit()
    except Exception:
        logger.warning("Cache write failed for activity_id=%s", activity_id)


def get_activity_list(cache_key: str) -> list | None:
    return _cache_get("activity_list", cache_key, _SHORT_TTL)


def set_activity_list(cache_key: str, data: list) -> None:
    _cache_set("activity_list", cache_key, data)


def get_daily_data(cache_key: str) -> dict | None:
    return _cache_get("daily_data", cache_key, _SHORT_TTL)


def set_daily_data(cache_key: str, data: dict) -> None:
    _cache_set("daily_data", cache_key, data)


def get_static_data(cache_key: str) -> dict | list | None:
    return _cache_get("static_data", cache_key, _STATIC_TTL)


def set_static_data(cache_key: str, data: dict | list) -> None:
    _cache_set("static_data", cache_key, data)
