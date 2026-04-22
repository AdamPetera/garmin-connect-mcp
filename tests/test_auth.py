from unittest.mock import patch
import pytest
from garmin_mcp.auth import setup_main


def test_setup_main_prompts_and_saves_tokens(monkeypatch, tmp_path):
    monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
    with patch("garmin_mcp.auth.input", return_value="test@example.com"), \
         patch("garmin_mcp.auth.getpass.getpass", return_value="testpass"), \
         patch("garmin_mcp.auth.Garmin") as MockGarmin:
        instance = MockGarmin.return_value
        setup_main()
    MockGarmin.assert_called_once_with("test@example.com", "testpass")
    instance.login.assert_called_once()
    instance.garth.dump.assert_called_once_with(str(tmp_path))


def test_setup_main_warns_if_token_save_fails(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
    with patch("garmin_mcp.auth.input", return_value="test@example.com"), \
         patch("garmin_mcp.auth.getpass.getpass", return_value="testpass"), \
         patch("garmin_mcp.auth.Garmin") as MockGarmin:
        instance = MockGarmin.return_value
        instance.garth.dump.side_effect = OSError("permission denied")
        setup_main()
    captured = capsys.readouterr()
    assert "Warning" in captured.out
