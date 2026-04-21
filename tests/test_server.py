from unittest.mock import patch
import pytest
from garmin_mcp import cache


@pytest.fixture(autouse=True)
def reset_client():
    import garmin_mcp.server as server
    server._client = None
    yield
    server._client = None


@pytest.fixture(autouse=True)
def tmp_cache(tmp_path):
    cache._db_path = tmp_path / "test.db"


@pytest.fixture
def mock_garmin_client():
    with patch("garmin_mcp.server.garmin.GarminClient") as MockClient:
        yield MockClient.return_value


def test_get_last_activity_fetches_details_and_caches(mock_garmin_client):
    from garmin_mcp.server import get_last_activity
    mock_garmin_client.get_last_activity.return_value = {"activityId": "1"}
    mock_garmin_client.get_activity_details.return_value = {"activityId": "1", "laps": []}
    result = get_last_activity()
    assert result == {"activityId": "1", "laps": []}
    mock_garmin_client.get_activity_details.assert_called_once_with("1")


def test_get_last_activity_uses_detail_cache_on_second_call(mock_garmin_client):
    from garmin_mcp.server import get_last_activity
    cache.set_activity_details("1", {"activityId": "1", "cached": True})
    mock_garmin_client.get_last_activity.return_value = {"activityId": "1"}
    result = get_last_activity()
    assert result["cached"] is True
    mock_garmin_client.get_activity_details.assert_not_called()


def test_get_last_activity_returns_empty_when_garmin_has_none(mock_garmin_client):
    from garmin_mcp.server import get_last_activity
    mock_garmin_client.get_last_activity.return_value = {}
    assert get_last_activity() == {}


def test_get_last_activity_returns_empty_when_activity_missing_id(mock_garmin_client):
    from garmin_mcp.server import get_last_activity
    mock_garmin_client.get_last_activity.return_value = {"activityName": "Run"}
    assert get_last_activity() == {}
    mock_garmin_client.get_activity_details.assert_not_called()


def test_get_activities_fetches_and_caches(mock_garmin_client):
    from garmin_mcp.server import get_activities
    mock_garmin_client.get_activities.return_value = [{"activityId": "1"}]
    result = get_activities("2026-04-01", "2026-04-21")
    assert result == [{"activityId": "1"}]
    mock_garmin_client.get_activities.assert_called_once_with("2026-04-01", "2026-04-21", None)


def test_get_activities_uses_cache(mock_garmin_client):
    from garmin_mcp.server import get_activities
    cache.set_activity_list("2026-04-01:2026-04-21:", [{"activityId": "cached"}])
    result = get_activities("2026-04-01", "2026-04-21")
    assert result[0]["activityId"] == "cached"
    mock_garmin_client.get_activities.assert_not_called()


def test_get_activities_defaults_end_date_to_today(mock_garmin_client):
    from datetime import date
    from garmin_mcp.server import get_activities
    mock_garmin_client.get_activities.return_value = []
    get_activities("2026-04-01")
    call_args = mock_garmin_client.get_activities.call_args
    assert call_args[0][1] == date.today().isoformat()


def test_get_activities_passes_type_filter(mock_garmin_client):
    from garmin_mcp.server import get_activities
    mock_garmin_client.get_activities.return_value = []
    get_activities("2026-04-01", "2026-04-21", "running")
    mock_garmin_client.get_activities.assert_called_once_with("2026-04-01", "2026-04-21", "running")


def test_get_activity_details_fetches_and_caches(mock_garmin_client):
    from garmin_mcp.server import get_activity_details
    mock_garmin_client.get_activity_details.return_value = {"activityId": "42", "laps": []}
    result = get_activity_details("42")
    assert result["activityId"] == "42"
    mock_garmin_client.get_activity_details.assert_called_once_with("42")


def test_get_activity_details_uses_cache(mock_garmin_client):
    from garmin_mcp.server import get_activity_details
    cache.set_activity_details("42", {"activityId": "42", "cached": True})
    result = get_activity_details("42")
    assert result["cached"] is True
    mock_garmin_client.get_activity_details.assert_not_called()
