from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from campaign_logger.cli import main


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("CL_GENERATOR_TOKEN", "mock_token")
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "mock_id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "mock_secret")


@pytest.fixture
def runner():
    return CliRunner()


class MockResource(MagicMock):
    """Mock for JSON API Resource."""

    def __init__(self, data, *args, **kwargs):
        """Initialize MockResource."""
        super().__init__(*args, **kwargs)
        self._data = data

    def to_dict(self):
        """Return dict representation."""
        return self._data

    def save(self):
        """Mock save method."""
        return self


@pytest.fixture
def mock_logger_client(mocker):
    mock_instance = MagicMock()
    mock_c1 = MockResource({"id": "c1"})
    mock_l1 = MockResource({"id": "l1"})
    mock_le1 = MockResource({"id": "le1"})
    mock_ce1 = MockResource({"id": "ce1"})

    mock_instance.get_campaigns.return_value = [mock_c1]
    mock_instance.get_campaign.return_value = mock_c1
    mock_instance.create_campaign.return_value = mock_c1
    mock_instance.update_campaign.return_value = mock_c1

    mock_instance.get_logs.return_value = [mock_l1]
    mock_instance.get_log.return_value = mock_l1
    mock_instance.create_log.return_value = mock_l1
    mock_instance.update_log.return_value = mock_l1

    mock_instance.get_log_entries.return_value = [mock_le1]
    mock_instance.get_log_entry.return_value = mock_le1
    mock_instance.create_log_entry.return_value = mock_le1
    mock_instance.update_log_entry.return_value = mock_le1

    mock_instance.get_campaign_entries.return_value = [mock_ce1]
    mock_instance.get_campaign_entry.return_value = mock_ce1
    mock_instance.create_campaign_entry.return_value = mock_ce1
    mock_instance.update_campaign_entry.return_value = mock_ce1

    mocker.patch("campaign_logger.cli.LoggerClient", return_value=mock_instance)
    return mock_instance


def test_list_campaigns(runner, mock_logger_client):
    mock_logger_client.get_campaigns.return_value = [type("MockCamp", (), {"id": "c1", "title": "Camp Title"})()]
    result = runner.invoke(main, ["logger", "campaign", "list"])
    assert result.exit_code == 0  # nosec
    assert "c1: Camp Title" in result.output  # nosec
    mock_logger_client.get_campaigns.assert_called_once()


def test_create_campaign(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "campaign", "create", "Title"])
    assert result.exit_code == 0  # nosec
    assert '"c1"' in result.output  # nosec
    mock_logger_client.create_campaign.assert_called_once_with("Title", "")


def test_update_campaign(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "campaign", "update", "c1", "--title", "New Title", "--description", "Desc"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_campaign.assert_called_once_with("c1")


def test_update_log(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "log", "update", "l1", "--title", "New Title", "--description", "Desc"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_log.assert_called_with("l1")


def test_update_entry(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "entry", "update", "le1", "text"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_log_entry.assert_called_with("le1")


def test_update_page(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "page", "update", "ce1", "text"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_campaign_entry.assert_called_with("ce1")


def test_delete_campaign(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "campaign", "delete", "c1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.delete_campaign.assert_called_once_with("c1")


def test_list_logs(runner, mock_logger_client):
    mock_logger_client.get_logs.return_value = [type("MockLog", (), {"id": "l1", "title": "Log Title"})()]
    result = runner.invoke(main, ["logger", "log", "list"])
    assert result.exit_code == 0  # nosec
    assert "l1: Log Title" in result.output  # nosec
    mock_logger_client.get_logs.assert_called_once()


def test_get_log(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "log", "get", "l1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_log.assert_called_once_with("l1")


def test_delete_log(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "log", "delete", "l1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.delete_log.assert_called_once_with("l1")


def test_list_entries(runner, mock_logger_client):
    mock_logger_client.get_log_entries.return_value = [
        type("MockEntry", (), {"id": "1", "log_id": "l1", "raw_text": "Text 1"})(),
        type("MockEntry", (), {"id": "2", "log_id": "l2", "raw_text": ""})(),
    ]
    result = runner.invoke(main, ["logger", "entry", "list"])
    assert result.exit_code == 0  # nosec
    assert "1: Text 1" in result.output  # nosec
    assert "2: (empty)" in result.output  # nosec
    mock_logger_client.get_log_entries.assert_called_once()

    result_filtered = runner.invoke(main, ["logger", "entry", "list", "l1"])
    assert result_filtered.exit_code == 0  # nosec
    assert "1: Text 1" in result_filtered.output  # nosec
    assert "2: (empty)" not in result_filtered.output  # nosec

    # Test filtering by env var
    import os
    os.environ["CL_DEFAULT_LOG_ID"] = "l2"
    result_env_filtered = runner.invoke(main, ["logger", "entry", "list"])
    assert result_env_filtered.exit_code == 0  # nosec
    assert "2: (empty)" in result_env_filtered.output  # nosec
    assert "1: Text 1" not in result_env_filtered.output  # nosec
    del os.environ["CL_DEFAULT_LOG_ID"]


def test_get_entry(runner, mock_logger_client):
    mock_logger_client.get_log_entry.return_value = type("MockEntry", (), {"id": "le1", "raw_text": "# Markdown"})()
    result = runner.invoke(main, ["logger", "entry", "get", "le1", "--raw"])
    assert result.exit_code == 0  # nosec
    assert "# Markdown" in result.output  # nosec
    mock_logger_client.get_log_entry.assert_called_once_with("le1")


def test_delete_entry(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "entry", "delete", "le1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.delete_log_entry.assert_called_once_with("le1")


def test_list_pages(runner, mock_logger_client):
    mock_logger_client.get_campaign_entries.return_value = [
        type("MockPage", (), {"id": "1", "campaign_id": "c1", "raw_text": "Page 1\nSecond line"})(),
        type("MockPage", (), {"id": "2", "campaign_id": "c2", "raw_text": ""})(),
    ]
    result = runner.invoke(main, ["logger", "page", "list"])
    assert result.exit_code == 0  # nosec
    assert "1: Page 1" in result.output  # nosec
    assert "Second line" not in result.output  # nosec
    assert "2: (empty)" in result.output  # nosec
    mock_logger_client.get_campaign_entries.assert_called_once()

    result_filtered = runner.invoke(main, ["logger", "page", "list", "c1"])
    assert result_filtered.exit_code == 0  # nosec
    assert "1: Page 1" in result_filtered.output  # nosec
    assert "2: (empty)" not in result_filtered.output  # nosec

    # Test filtering by env var
    import os
    os.environ["CL_DEFAULT_CAMPAIGN_ID"] = "c2"
    result_env_filtered = runner.invoke(main, ["logger", "page", "list"])
    assert result_env_filtered.exit_code == 0  # nosec
    assert "2: (empty)" in result_env_filtered.output  # nosec
    assert "1: Page 1" not in result_env_filtered.output  # nosec
    del os.environ["CL_DEFAULT_CAMPAIGN_ID"]


def test_get_page(runner, mock_logger_client):
    mock_logger_client.get_campaign_entry.return_value = type("MockPage", (), {"id": "ce1", "raw_text": "# Markdown"})()
    result = runner.invoke(main, ["logger", "page", "get", "ce1", "--raw"])
    assert result.exit_code == 0  # nosec
    assert "# Markdown" in result.output  # nosec
    mock_logger_client.get_campaign_entry.assert_called_once_with("ce1")


def test_delete_page(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "page", "delete", "ce1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.delete_campaign_entry.assert_called_once_with("ce1")


def test_create_log(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "log", "create", "c1", "Log Title"])
    assert result.exit_code == 0  # nosec
    assert '"l1"' in result.output  # nosec
    mock_logger_client.create_log.assert_called_once_with("c1", "Log Title", "")


def test_create_entry(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "entry", "create", "l1", "text"])
    assert result.exit_code == 0  # nosec
    assert '"le1"' in result.output  # nosec
    mock_logger_client.create_log_entry.assert_called_once_with("l1", "text")


def test_create_page(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "page", "create", "c1", "text"])
    assert result.exit_code == 0  # nosec
    assert '"ce1"' in result.output  # nosec
    mock_logger_client.create_campaign_entry.assert_called_once_with("c1", "text")


def test_logger_cli_error_handling(runner, mock_logger_client):
    mock_logger_client.get_campaigns.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "campaign", "list"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_campaign.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "campaign", "get", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.create_campaign.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "campaign", "create", "title"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_campaign.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "campaign", "update", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.delete_campaign.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "campaign", "delete", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_logs.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "log", "list"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_log.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "log", "get", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.create_log.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "log", "create", "1", "title"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_log.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "log", "update", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.delete_log.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "log", "delete", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_log_entries.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "entry", "list"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_log_entry.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "entry", "get", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.create_log_entry.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "entry", "create", "1", "text"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_log_entry.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "entry", "update", "1", "text"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.delete_log_entry.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "entry", "delete", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_campaign_entries.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "page", "list"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_campaign_entry.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "page", "get", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.create_campaign_entry.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "page", "create", "1", "text"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_campaign_entry.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "page", "update", "1", "text"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.delete_campaign_entry.side_effect = Exception("API error")
    result = runner.invoke(main, ["logger", "page", "delete", "1"])
    assert "Error: API error" in result.output  # nosec
