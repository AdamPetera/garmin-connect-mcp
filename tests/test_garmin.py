from unittest.mock import patch, MagicMock
import pytest
from garmin_mcp.garmin import GarminClient


@pytest.fixture
def mock_api():
    with patch("garmin_mcp.garmin.Garmin") as MockGarmin:
        instance = MockGarmin.return_value
        instance.login.return_value = None
        instance.garth.load.side_effect = FileNotFoundError
        yield instance


@pytest.fixture
def client(mock_api, monkeypatch, tmp_path):
    monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
    monkeypatch.setenv("GARMIN_EMAIL", "test@example.com")
    monkeypatch.setenv("GARMIN_PASSWORD", "testpass")
    return GarminClient()


def test_raises_when_login_fails_without_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
    monkeypatch.delenv("GARMIN_EMAIL", raising=False)
    monkeypatch.delenv("GARMIN_PASSWORD", raising=False)
    with patch("garmin_mcp.garmin.Garmin") as MockGarmin:
        MockGarmin.return_value.login.side_effect = Exception("no tokens")
        with pytest.raises(RuntimeError, match="garmin-mcp-setup"):
            GarminClient()


def test_raises_original_error_when_login_fails_with_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
    monkeypatch.setenv("GARMIN_EMAIL", "test@example.com")
    monkeypatch.setenv("GARMIN_PASSWORD", "testpass")
    with patch("garmin_mcp.garmin.Garmin") as MockGarmin:
        MockGarmin.return_value.login.side_effect = Exception("auth failed")
        with pytest.raises(Exception, match="auth failed"):
            GarminClient()


def test_get_last_activity_returns_first_result(client, mock_api):
    mock_api.get_activities.return_value = [{"activityId": "1", "activityName": "Run"}]
    result = client.get_last_activity()
    assert result == {"activityId": "1", "activityName": "Run"}
    mock_api.get_activities.assert_called_once_with(0, 1)


def test_get_last_activity_returns_empty_when_none(client, mock_api):
    mock_api.get_activities.return_value = []
    assert client.get_last_activity() == {}


def test_get_activities_no_type_filter(client, mock_api):
    expected = [{"activityId": "1"}, {"activityId": "2"}]
    mock_api.get_activities_by_date.return_value = expected
    result = client.get_activities("2026-04-01", "2026-04-21")
    assert result == expected
    mock_api.get_activities_by_date.assert_called_once_with("2026-04-01", "2026-04-21", None)


def test_get_activities_with_type_filter(client, mock_api):
    mock_api.get_activities_by_date.return_value = []
    client.get_activities("2026-04-01", "2026-04-21", "running")
    mock_api.get_activities_by_date.assert_called_once_with("2026-04-01", "2026-04-21", "running")


def test_get_activity_details(client, mock_api):
    expected = {"activityId": "42", "laps": [{"lapIndex": 1}]}
    mock_api.get_activity.return_value = expected
    result = client.get_activity_details("42")
    assert result == expected
    mock_api.get_activity.assert_called_once_with("42")


def test_get_last_activity_retries_once_on_failure(client, mock_api):
    mock_api.get_activities.side_effect = [Exception("timeout"), [{"activityId": "1"}]]
    with patch("garmin_mcp.garmin.time.sleep") as mock_sleep:
        result = client.get_last_activity()
    assert result == {"activityId": "1"}
    assert mock_api.get_activities.call_count == 2
    mock_sleep.assert_called_once_with(2)


def test_get_last_activity_raises_after_two_failures(client, mock_api):
    mock_api.get_activities.side_effect = Exception("rate limited")
    with patch("garmin_mcp.garmin.time.sleep") as mock_sleep:
        with pytest.raises(RuntimeError, match="rate limited"):
            client.get_last_activity()
    mock_sleep.assert_called_once_with(2)


def test_login_called_with_token_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
    monkeypatch.setenv("GARMIN_EMAIL", "test@example.com")
    monkeypatch.setenv("GARMIN_PASSWORD", "testpass")
    with patch("garmin_mcp.garmin.Garmin") as MockGarmin:
        instance = MockGarmin.return_value
        GarminClient()
    instance.login.assert_called_once_with(tokenstore=str(tmp_path))


def test_garmin_constructed_with_credentials_when_provided(monkeypatch, tmp_path):
    monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
    monkeypatch.setenv("GARMIN_EMAIL", "test@example.com")
    monkeypatch.setenv("GARMIN_PASSWORD", "testpass")
    with patch("garmin_mcp.garmin.Garmin") as MockGarmin:
        GarminClient()
    MockGarmin.assert_called_once_with("test@example.com", "testpass")


def test_garmin_constructed_without_credentials_when_not_provided(monkeypatch, tmp_path):
    monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
    monkeypatch.delenv("GARMIN_EMAIL", raising=False)
    monkeypatch.delenv("GARMIN_PASSWORD", raising=False)
    with patch("garmin_mcp.garmin.Garmin") as MockGarmin:
        MockGarmin.return_value.login.return_value = None  # login succeeds
        GarminClient()
    MockGarmin.assert_called_once_with()


def test_get_daily_wellness_calls_all_endpoints(client, mock_api):
    mock_api.get_stats.return_value = {"totalSteps": 8000}
    mock_api.get_sleep_data.return_value = {"dailySleepDTO": {"sleepScore": 78}}
    mock_api.get_body_battery.return_value = [{"charged": 85, "drained": 15}]
    mock_api.get_hrv_data.return_value = {"hrvSummary": {"lastNight": 55}}
    mock_api.get_rhr_day.return_value = {"restingHeartRate": 52}

    result = client.get_daily_wellness("2026-04-23")

    assert result["stats"] == {"totalSteps": 8000}
    assert result["sleep"] == {"dailySleepDTO": {"sleepScore": 78}}
    assert result["body_battery"] == [{"charged": 85, "drained": 15}]
    assert result["hrv"] == {"hrvSummary": {"lastNight": 55}}
    assert result["resting_hr"] == {"restingHeartRate": 52}
    mock_api.get_stats.assert_called_once_with("2026-04-23")
    mock_api.get_sleep_data.assert_called_once_with("2026-04-23")
    mock_api.get_body_battery.assert_called_once_with("2026-04-23")
    mock_api.get_hrv_data.assert_called_once_with("2026-04-23")
    mock_api.get_rhr_day.assert_called_once_with("2026-04-23")


def test_get_training_status_calls_both_endpoints(client, mock_api):
    mock_api.get_training_readiness.return_value = {"score": 72, "level": "GOOD"}
    mock_api.get_training_status.return_value = {"trainingStatusDTO": {"latestTrainingStatusVO": {"trainingStatus": "MAINTAINING"}}}

    result = client.get_training_status("2026-04-23")

    assert result["readiness"] == {"score": 72, "level": "GOOD"}
    assert result["status"] == {"trainingStatusDTO": {"latestTrainingStatusVO": {"trainingStatus": "MAINTAINING"}}}
    mock_api.get_training_readiness.assert_called_once_with("2026-04-23")
    mock_api.get_training_status.assert_called_once_with("2026-04-23")


def test_get_race_predictions_returns_result(client, mock_api):
    mock_api.get_race_predictions.return_value = {"racePredictions": [{"raceDistance": "5K", "timePrediction": 1500}]}
    result = client.get_race_predictions()
    assert result == {"racePredictions": [{"raceDistance": "5K", "timePrediction": 1500}]}
    mock_api.get_race_predictions.assert_called_once_with()


def test_get_personal_records_returns_result(client, mock_api):
    mock_api.get_personal_record.return_value = {"personalRecords": [{"typeId": 1, "value": 300}]}
    result = client.get_personal_records()
    assert result == {"personalRecords": [{"typeId": 1, "value": 300}]}
    mock_api.get_personal_record.assert_called_once_with()
