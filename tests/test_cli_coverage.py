import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from campaign_logger.cli import load_config
from campaign_logger.cli import main


@pytest.fixture
def runner():
    return CliRunner()


def test_load_config_success(tmp_path, monkeypatch):
    """Test load_config successfully reads secrets from the file."""
    config_file = tmp_path / ".campaign_logger.json"
    config_data = {
        "token": "file_token",
        "client_id": "file_client_id",
        "client_secret": "file_client_secret",
        "default_campaign_id": "file_campaign",
        "default_log_id": "file_log",
    }
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    # Remove env vars to ensure they get loaded from the config
    for key in ["CL_GENERATOR_TOKEN", "CL_LOGGER_CLIENT_ID", "CL_LOGGER_CLIENT_SECRET", "CL_DEFAULT_CAMPAIGN_ID", "CL_DEFAULT_LOG_ID"]:
        monkeypatch.delenv(key, raising=False)

    with patch.object(Path, "home", return_value=tmp_path):
        load_config()

    assert os.environ["CL_GENERATOR_TOKEN"] == "file_token"
    assert os.environ["CL_LOGGER_CLIENT_ID"] == "file_client_id"
    assert os.environ["CL_LOGGER_CLIENT_SECRET"] == "file_client_secret"
    assert os.environ["CL_DEFAULT_CAMPAIGN_ID"] == "file_campaign"
    assert os.environ["CL_DEFAULT_LOG_ID"] == "file_log"

    # Test failure does not crash
    config_file.unlink()
    with open(config_file, "w") as f:
        f.write("invalid json")
    with patch.object(Path, "home", return_value=tmp_path):
        load_config()  # Should silently catch json.decoder.JSONDecodeError


def test_missing_auth_tokens(runner, monkeypatch):
    """Test graceful failures when auth arguments are missing."""
    monkeypatch.delenv("CL_GENERATOR_TOKEN", raising=False)
    monkeypatch.delenv("CL_LOGGER_CLIENT_ID", raising=False)
    monkeypatch.delenv("CL_LOGGER_CLIENT_SECRET", raising=False)

    result = runner.invoke(main, ["generator", "list"])
    assert result.exit_code == 1
    assert "Error: No authentication token provided" in result.output

    result = runner.invoke(main, ["logger", "campaign", "list"])
    assert result.exit_code == 1
    assert "Error: Missing client ID or secret" in result.output


def test_rich_import_error(runner, monkeypatch, mocker):
    """Test fallback when rich is not installed."""
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")

    mock_instance = MagicMock()
    mock_instance.get_log_entry.return_value = type(
        "MockEntry", (), {"id": "1", "raw_text": "text", "to_dict": lambda *args: {"id": "1", "raw_text": "text"}}
    )()
    mock_instance.get_campaign_entry.return_value = type(
        "MockPage", (), {"id": "1", "raw_text": "text", "to_dict": lambda *args: {"id": "1", "raw_text": "text"}}
    )()
    mocker.patch("campaign_logger.cli.LoggerClient", return_value=mock_instance)

    # Hide rich module
    with patch.dict(sys.modules, {"rich.console": None, "rich.markdown": None}):
        result = runner.invoke(main, ["logger", "entry", "get", "1"])
        assert result.exit_code == 0
        assert "text" in result.output

        result = runner.invoke(main, ["logger", "page", "get", "1"])
        assert result.exit_code == 0
        assert "text" in result.output


def test_http_error_re_raised(runner, monkeypatch, mocker):
    import requests

    monkeypatch.setenv("CL_GENERATOR_TOKEN", "token")
    mock_instance = MagicMock()
    mocker.patch("campaign_logger.cli.GeneratorClient", return_value=mock_instance)

    response = requests.Response()
    response.status_code = 500
    mock_instance.get_generator.side_effect = requests.exceptions.HTTPError("Internal error", response=response)
    mock_instance.get_generator_by_name.side_effect = requests.exceptions.HTTPError("Internal error", response=response)

    result = runner.invoke(main, ["generator", "get", "1"])
    assert result.exit_code == 0
    assert "Internal error" in result.output

    mock_instance.execute_operation.side_effect = requests.exceptions.HTTPError("Internal error", response=response)
    result = runner.invoke(main, ["generator", "generate", "1"])
    assert result.exit_code == 0
    assert "Internal error" in result.output

    result = runner.invoke(main, ["generator", "validate", "1"])
    assert result.exit_code == 0
    assert "Internal error" in result.output


def test_generator_name_lookup_failed(runner, monkeypatch, mocker):
    import requests

    monkeypatch.setenv("CL_GENERATOR_TOKEN", "token")
    mock_instance = MagicMock()
    mocker.patch("campaign_logger.cli.GeneratorClient", return_value=mock_instance)

    response = requests.Response()
    response.status_code = 404

    mock_instance.execute_operation.side_effect = requests.exceptions.HTTPError("Not found", response=response)
    mock_instance.get_generator.side_effect = requests.exceptions.HTTPError("Not found", response=response)
    mock_instance.get_generator_by_name.return_value = None

    result = runner.invoke(main, ["generator", "generate", "1"])
    assert "Error: Generator not found by ID or Name" in result.output

    result = runner.invoke(main, ["generator", "validate", "1"])
    assert "Error: Generator not found by ID or Name" in result.output
