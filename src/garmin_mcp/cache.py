import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

_db_path: Path = Path.home() / ".garmin_mcp_cache.db"
_LIST_TTL = timedelta(hours=1)
_DAILY_TTL = timedelta(hours=1)
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


def get_activity_details(activity_id: str) -> dict | None:
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT data FROM activity_details WHERE activity_id = ?",
                (str(activity_id),),
            ).fetchone()
            return json.loads(row[0]) if row else None
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
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT data, fetched_at FROM activity_list WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
            if not row:
                return None
            fetched_at = datetime.fromisoformat(row[1])
            if datetime.now(UTC) - fetched_at > _LIST_TTL:
                return None
            return json.loads(row[0])
    except Exception:
        logger.warning("Cache read failed for cache_key=%s", cache_key)
        return None


def set_activity_list(cache_key: str, data: list) -> None:
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO activity_list VALUES (?, ?, ?)",
                (cache_key, json.dumps(data), datetime.now(UTC).isoformat()),
            )
            conn.commit()
    except Exception:
        logger.warning("Cache write failed for cache_key=%s", cache_key)


def get_daily_data(cache_key: str) -> dict | None:
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT data, fetched_at FROM daily_data WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
            if not row:
                return None
            fetched_at = datetime.fromisoformat(row[1])
            if datetime.now(UTC) - fetched_at > _DAILY_TTL:
                return None
            return json.loads(row[0])
    except Exception:
        logger.warning("Cache read failed for daily_data key=%s", cache_key)
        return None


def set_daily_data(cache_key: str, data: dict) -> None:
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO daily_data VALUES (?, ?, ?)",
                (cache_key, json.dumps(data), datetime.now(UTC).isoformat()),
            )
            conn.commit()
    except Exception:
        logger.warning("Cache write failed for daily_data key=%s", cache_key)


def get_static_data(cache_key: str) -> dict | list | None:
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT data, fetched_at FROM static_data WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
            if not row:
                return None
            fetched_at = datetime.fromisoformat(row[1])
            if datetime.now(UTC) - fetched_at > _STATIC_TTL:
                return None
            return json.loads(row[0])
    except Exception:
        logger.warning("Cache read failed for static_data key=%s", cache_key)
        return None


def set_static_data(cache_key: str, data: dict | list) -> None:
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO static_data VALUES (?, ?, ?)",
                (cache_key, json.dumps(data), datetime.now(UTC).isoformat()),
            )
            conn.commit()
    except Exception:
        logger.warning("Cache write failed for static_data key=%s", cache_key)
