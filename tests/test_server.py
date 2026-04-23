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


def test_get_daily_wellness_fetches_and_caches(mock_garmin_client):
    from garmin_mcp.server import get_daily_wellness
    mock_garmin_client.get_daily_wellness.return_value = {"stats": {"totalSteps": 8000}, "sleep": {}, "body_battery": [], "hrv": None, "resting_hr": {}}
    result = get_daily_wellness("2026-04-23")
    assert result["stats"] == {"totalSteps": 8000}
    mock_garmin_client.get_daily_wellness.assert_called_once_with("2026-04-23")


def test_get_daily_wellness_uses_cache(mock_garmin_client):
    from garmin_mcp.server import get_daily_wellness
    cached = {"stats": {"totalSteps": 5000}, "sleep": {}, "body_battery": [], "hrv": None, "resting_hr": {}}
    cache.set_daily_data("wellness:2026-04-23", cached)
    result = get_daily_wellness("2026-04-23")
    assert result["stats"]["totalSteps"] == 5000
    mock_garmin_client.get_daily_wellness.assert_not_called()


def test_get_daily_wellness_defaults_to_today(mock_garmin_client):
    from datetime import date
    from garmin_mcp.server import get_daily_wellness
    mock_garmin_client.get_daily_wellness.return_value = {"stats": {}, "sleep": {}, "body_battery": [], "hrv": None, "resting_hr": {}}
    get_daily_wellness()
    mock_garmin_client.get_daily_wellness.assert_called_once_with(date.today().isoformat())


def test_get_training_status_fetches_and_caches(mock_garmin_client):
    from garmin_mcp.server import get_training_status
    mock_garmin_client.get_training_status.return_value = {"readiness": {"score": 72}, "status": {}}
    result = get_training_status("2026-04-23")
    assert result["readiness"]["score"] == 72
    mock_garmin_client.get_training_status.assert_called_once_with("2026-04-23")


def test_get_training_status_uses_cache(mock_garmin_client):
    from garmin_mcp.server import get_training_status
    cached = {"readiness": {"score": 55}, "status": {}}
    cache.set_daily_data("training:2026-04-23", cached)
    result = get_training_status("2026-04-23")
    assert result["readiness"]["score"] == 55
    mock_garmin_client.get_training_status.assert_not_called()


def test_get_training_status_defaults_to_today(mock_garmin_client):
    from datetime import date
    from garmin_mcp.server import get_training_status
    mock_garmin_client.get_training_status.return_value = {"readiness": {}, "status": {}}
    get_training_status()
    mock_garmin_client.get_training_status.assert_called_once_with(date.today().isoformat())


def test_get_race_predictions_fetches_and_caches(mock_garmin_client):
    from garmin_mcp.server import get_race_predictions
    mock_garmin_client.get_race_predictions.return_value = {"racePredictions": []}
    result = get_race_predictions()
    assert result == {"racePredictions": []}
    mock_garmin_client.get_race_predictions.assert_called_once_with()


def test_get_race_predictions_uses_cache(mock_garmin_client):
    from garmin_mcp.server import get_race_predictions
    cache.set_static_data("race_predictions", {"racePredictions": [{"distance": "5K"}]})
    result = get_race_predictions()
    assert result["racePredictions"][0]["distance"] == "5K"
    mock_garmin_client.get_race_predictions.assert_not_called()


def test_get_personal_records_fetches_and_caches(mock_garmin_client):
    from garmin_mcp.server import get_personal_records
    mock_garmin_client.get_personal_records.return_value = {"personalRecords": []}
    result = get_personal_records()
    assert result == {"personalRecords": []}
    mock_garmin_client.get_personal_records.assert_called_once_with()


def test_get_personal_records_uses_cache(mock_garmin_client):
    from garmin_mcp.server import get_personal_records
    cache.set_static_data("personal_records", {"personalRecords": [{"type": "running"}]})
    result = get_personal_records()
    assert result["personalRecords"][0]["type"] == "running"
    mock_garmin_client.get_personal_records.assert_not_called()
