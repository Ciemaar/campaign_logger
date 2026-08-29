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
    result = runner.invoke(main, ["generator", "get", "1"])
    assert "Error: Generator not found by ID or Name" in result.output

    result = runner.invoke(main, ["generator", "generate", "1"])
    assert "Error: Generator not found by ID or Name" in result.output

    result = runner.invoke(main, ["generator", "validate", "1"])
    assert "Error: Generator not found by ID or Name" in result.output

    result = runner.invoke(main, ["generator", "get", "1"])
    assert "Error: Generator not found by ID or Name" in result.output


def test_missing_client_config(runner, monkeypatch):
    monkeypatch.delenv("CL_LOGGER_CLIENT_ID", raising=False)
    monkeypatch.delenv("CL_LOGGER_CLIENT_SECRET", raising=False)
    result = runner.invoke(main, ["logger", "campaign", "list"])
    assert result.exit_code == 1


def test_missing_token_config(runner, monkeypatch):
    monkeypatch.delenv("CL_GENERATOR_TOKEN", raising=False)
    result = runner.invoke(main, ["generator", "list"])
    assert result.exit_code == 1


def test_json_errors_ignored(tmp_path, monkeypatch):
    config_file = tmp_path / ".campaign_logger.json"
    with open(config_file, "w") as f:
        f.write("invalid json")
    with patch.object(Path, "home", return_value=tmp_path):
        load_config()


def test_list_entries_with_default_log_id(runner, monkeypatch, mocker):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    monkeypatch.setenv("CL_DEFAULT_LOG_ID", "1")

    mock_instance = MagicMock()
    mock_instance.get_log_entries.return_value = [type("MockEntry", (), {"id": "1", "log_id": "1", "raw_text": "text1"})()]
    mocker.patch("campaign_logger.cli.LoggerClient", return_value=mock_instance)

    result = runner.invoke(main, ["logger", "entry", "list"])
    assert result.exit_code == 0
    assert "text1" in result.output
    assert "text2" not in result.output


def test_list_pages_with_default_campaign_id(runner, monkeypatch, mocker):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    monkeypatch.setenv("CL_DEFAULT_CAMPAIGN_ID", "1")

    mock_instance = MagicMock()
    mock_instance.get_campaign_entries.return_value = [type("MockPage", (), {"id": "1", "campaign_id": "1", "raw_text": "text1"})()]
    mocker.patch("campaign_logger.cli.LoggerClient", return_value=mock_instance)

    result = runner.invoke(main, ["logger", "page", "list"])
    assert result.exit_code == 0
    assert "text1" in result.output
    assert "text2" not in result.output


def test_list_entries_no_log_id(runner, monkeypatch, mocker):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    monkeypatch.delenv("CL_DEFAULT_LOG_ID", raising=False)

    mock_instance = MagicMock()
    mock_instance.get_log_entries.return_value = [
        type("MockEntry", (), {"id": "1", "log_id": "1", "raw_text": "text1"})(),
        type("MockEntry", (), {"id": "2", "log_id": "2", "raw_text": None})(),
    ]
    mocker.patch("campaign_logger.cli.LoggerClient", return_value=mock_instance)

    result = runner.invoke(main, ["logger", "entry", "list"])
    assert result.exit_code == 0
    assert "1: text1" in result.output
    assert "2: (empty)" not in result.output


def test_list_pages_no_campaign_id(runner, monkeypatch, mocker):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    monkeypatch.delenv("CL_DEFAULT_CAMPAIGN_ID", raising=False)

    mock_instance = MagicMock()
    mock_instance.get_campaign_entries.return_value = [
        type("MockPage", (), {"id": "1", "campaign_id": "1", "raw_text": "text1"})(),
        type("MockPage", (), {"id": "2", "campaign_id": "2", "raw_text": None})(),
    ]
    mocker.patch("campaign_logger.cli.LoggerClient", return_value=mock_instance)

    result = runner.invoke(main, ["logger", "page", "list"])
    assert result.exit_code == 0
    assert "1: text1" in result.output
    assert "2: (empty)" not in result.output


def test_missing_config_file_handled(tmp_path, monkeypatch):
    """Test load_config successfully ignores missing config file."""
    config_file = tmp_path / ".campaign_logger.json"
    if config_file.exists():
        config_file.unlink()

    with patch.object(Path, "home", return_value=tmp_path):
        load_config()  # Should silently pass


def test_generator_validate_by_id_success(runner, monkeypatch, mocker):
    monkeypatch.setenv("CL_GENERATOR_TOKEN", "token")
    mock_instance = MagicMock()
    mocker.patch("campaign_logger.cli.GeneratorClient", return_value=mock_instance)
    mock_instance.execute_operation.return_value = {}

    result = runner.invoke(main, ["generator", "validate", "1"])
    assert result.exit_code == 0
    assert "Generator 1 is valid." in result.output


def test_get_entry_without_rich(runner, monkeypatch, mocker):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")

    mock_instance = MagicMock()
    mock_instance.get_log_entry.return_value = type("MockEntry", (), {"id": "1", "raw_text": "text1", "to_dict": lambda *args: {}})()
    mocker.patch("campaign_logger.cli.LoggerClient", return_value=mock_instance)

    result = runner.invoke(main, ["logger", "entry", "get", "1", "--raw"])
    assert result.exit_code == 0
    assert "text1" in result.output


def test_get_page_without_rich(runner, monkeypatch, mocker):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")

    mock_instance = MagicMock()
    mock_instance.get_campaign_entry.return_value = type("MockPage", (), {"id": "1", "raw_text": "text1", "to_dict": lambda *args: {}})()
    mocker.patch("campaign_logger.cli.LoggerClient", return_value=mock_instance)

    result = runner.invoke(main, ["logger", "page", "get", "1", "--raw"])
    assert result.exit_code == 0
    assert "text1" in result.output


def test_list_entries_no_first_line(runner, monkeypatch, mocker):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    monkeypatch.delenv("CL_DEFAULT_LOG_ID", raising=False)

    mock_instance = MagicMock()
    mock_instance.get_log_entries.return_value = [
        type("MockEntry", (), {"id": "1", "log_id": "1", "raw_text": ""})(),
    ]
    mocker.patch("campaign_logger.cli.LoggerClient", return_value=mock_instance)

    result = runner.invoke(main, ["logger", "entry", "list"])
    assert result.exit_code == 0
    assert "1: (empty)" not in result.output


def test_list_pages_no_first_line(runner, monkeypatch, mocker):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    monkeypatch.delenv("CL_DEFAULT_CAMPAIGN_ID", raising=False)

    mock_instance = MagicMock()
    mock_instance.get_campaign_entries.return_value = [
        type("MockPage", (), {"id": "1", "campaign_id": "1", "raw_text": ""})(),
    ]
    mocker.patch("campaign_logger.cli.LoggerClient", return_value=mock_instance)

    result = runner.invoke(main, ["logger", "page", "list"])
    assert result.exit_code == 0
    assert "1: (empty)" not in result.output
