import sqlite3
from datetime import UTC, datetime, timedelta
import pytest
from garmin_mcp import cache


@pytest.fixture(autouse=True)
def tmp_db(tmp_path):
    cache._db_path = tmp_path / "test.db"


def test_get_activity_details_returns_none_when_missing():
    assert cache.get_activity_details("123") is None


def test_set_and_get_activity_details():
    data = {"activityId": "123", "distance": 5000}
    cache.set_activity_details("123", data)
    assert cache.get_activity_details("123") == data


def test_activity_details_overwrite():
    cache.set_activity_details("1", {"v": 1})
    cache.set_activity_details("1", {"v": 2})
    assert cache.get_activity_details("1") == {"v": 2}


def test_activity_details_never_expires():
    data = {"activityId": "999"}
    cache.set_activity_details("999", data)
    old_time = (datetime.now(UTC) - timedelta(days=365)).isoformat()
    with sqlite3.connect(cache._db_path) as conn:
        conn.execute(
            "UPDATE activity_details SET fetched_at = ? WHERE activity_id = ?",
            (old_time, "999"),
        )
    assert cache.get_activity_details("999") == data


def test_get_activity_list_returns_none_when_missing():
    assert cache.get_activity_list("2026-01-01:2026-01-31:") is None


def test_set_and_get_activity_list():
    data = [{"activityId": "1"}, {"activityId": "2"}]
    cache.set_activity_list("key", data)
    assert cache.get_activity_list("key") == data


def test_activity_list_expires_after_one_hour():
    cache.set_activity_list("key", [{"activityId": "1"}])
    two_hours_ago = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    with sqlite3.connect(cache._db_path) as conn:
        conn.execute(
            "UPDATE activity_list SET fetched_at = ? WHERE cache_key = ?",
            (two_hours_ago, "key"),
        )
    assert cache.get_activity_list("key") is None


def test_activity_list_still_valid_within_one_hour():
    cache.set_activity_list("key", [{"activityId": "1"}])
    thirty_min_ago = (datetime.now(UTC) - timedelta(minutes=30)).isoformat()
    with sqlite3.connect(cache._db_path) as conn:
        conn.execute(
            "UPDATE activity_list SET fetched_at = ? WHERE cache_key = ?",
            (thirty_min_ago, "key"),
        )
    assert cache.get_activity_list("key") is not None


def test_get_daily_data_returns_none_when_missing():
    assert cache.get_daily_data("wellness:2026-04-23") is None


def test_set_and_get_daily_data():
    data = {"steps": 10000, "sleep_score": 85}
    cache.set_daily_data("wellness:2026-04-23", data)
    assert cache.get_daily_data("wellness:2026-04-23") == data


def test_daily_data_expires_after_one_hour():
    cache.set_daily_data("wellness:2026-04-01", {"steps": 5000})
    two_hours_ago = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    with sqlite3.connect(cache._db_path) as conn:
        conn.execute(
            "UPDATE daily_data SET fetched_at = ? WHERE cache_key = ?",
            (two_hours_ago, "wellness:2026-04-01"),
        )
    assert cache.get_daily_data("wellness:2026-04-01") is None


def test_daily_data_still_valid_within_one_hour():
    cache.set_daily_data("wellness:2026-04-01", {"steps": 5000})
    thirty_min_ago = (datetime.now(UTC) - timedelta(minutes=30)).isoformat()
    with sqlite3.connect(cache._db_path) as conn:
        conn.execute(
            "UPDATE daily_data SET fetched_at = ? WHERE cache_key = ?",
            (thirty_min_ago, "wellness:2026-04-01"),
        )
    assert cache.get_daily_data("wellness:2026-04-01") is not None


def test_get_static_data_returns_none_when_missing():
    assert cache.get_static_data("race_predictions") is None


def test_set_and_get_static_data():
    data = {"5K": "25:00", "10K": "52:00"}
    cache.set_static_data("race_predictions", data)
    assert cache.get_static_data("race_predictions") == data


def test_static_data_expires_after_four_hours():
    cache.set_static_data("personal_records", [{"type": "running", "pr": 120}])
    five_hours_ago = (datetime.now(UTC) - timedelta(hours=5)).isoformat()
    with sqlite3.connect(cache._db_path) as conn:
        conn.execute(
            "UPDATE static_data SET fetched_at = ? WHERE cache_key = ?",
            (five_hours_ago, "personal_records"),
        )
    assert cache.get_static_data("personal_records") is None


def test_static_data_still_valid_within_four_hours():
    cache.set_static_data("personal_records", [{"type": "running", "pr": 120}])
    two_hours_ago = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    with sqlite3.connect(cache._db_path) as conn:
        conn.execute(
            "UPDATE static_data SET fetched_at = ? WHERE cache_key = ?",
            (two_hours_ago, "personal_records"),
        )
    assert cache.get_static_data("personal_records") is not None
