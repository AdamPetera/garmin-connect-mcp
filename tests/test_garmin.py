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
def client(mock_api, monkeypatch):
    monkeypatch.setenv("GARMIN_EMAIL", "test@example.com")
    monkeypatch.setenv("GARMIN_PASSWORD", "testpass")
    return GarminClient()


def test_raises_without_email(monkeypatch):
    monkeypatch.delenv("GARMIN_EMAIL", raising=False)
    monkeypatch.delenv("GARMIN_PASSWORD", raising=False)
    with patch("garmin_mcp.garmin.Garmin") as MockGarmin:
        MockGarmin.return_value.garth.load.side_effect = FileNotFoundError
        with pytest.raises(RuntimeError, match="garmin-mcp-setup"):
            GarminClient()


def test_raises_without_password(monkeypatch):
    monkeypatch.setenv("GARMIN_EMAIL", "test@example.com")
    monkeypatch.delenv("GARMIN_PASSWORD", raising=False)
    with patch("garmin_mcp.garmin.Garmin") as MockGarmin:
        MockGarmin.return_value.garth.load.side_effect = FileNotFoundError
        with pytest.raises(RuntimeError, match="garmin-mcp-setup"):
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


def test_uses_garth_tokens_when_available(monkeypatch, tmp_path):
    monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
    monkeypatch.delenv("GARMIN_EMAIL", raising=False)
    monkeypatch.delenv("GARMIN_PASSWORD", raising=False)
    with patch("garmin_mcp.garmin.Garmin") as MockGarmin:
        instance = MockGarmin.return_value
        instance.garth.load.return_value = None  # tokens found — no side_effect
        client = GarminClient()
    instance.garth.load.assert_called_once_with(str(tmp_path))
    instance.login.assert_not_called()


def test_falls_back_to_env_creds_when_no_tokens(monkeypatch, tmp_path):
    monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
    monkeypatch.setenv("GARMIN_EMAIL", "test@example.com")
    monkeypatch.setenv("GARMIN_PASSWORD", "testpass")
    with patch("garmin_mcp.garmin.Garmin") as MockGarmin:
        instance = MockGarmin.return_value
        instance.garth.load.side_effect = FileNotFoundError
        GarminClient()
    instance.login.assert_called_once()
    instance.garth.dump.assert_called_once_with(str(tmp_path))


def test_raises_when_no_tokens_and_no_env_creds(monkeypatch, tmp_path):
    monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
    monkeypatch.delenv("GARMIN_EMAIL", raising=False)
    monkeypatch.delenv("GARMIN_PASSWORD", raising=False)
    with patch("garmin_mcp.garmin.Garmin") as MockGarmin:
        instance = MockGarmin.return_value
        instance.garth.load.side_effect = FileNotFoundError
        with pytest.raises(RuntimeError, match="garmin-mcp-setup"):
            GarminClient()
