from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from campaign_logger.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class MockResource:
    """Mock for JSON API Resource."""

    def __init__(self, data):
        """Initialize MockResource."""
        self._data = data

    def model_dump_json(self, **kwargs):
        """Return JSON representation."""
        import json

        return json.dumps(self._data)


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
    result = runner.invoke(main, ["logger", "campaign", "list"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_campaigns.assert_called_once()


def test_create_campaign(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "campaign", "create", "Title"])
    assert result.exit_code == 0  # nosec
    assert '"c1"' in result.output  # nosec
    mock_logger_client.create_campaign.assert_called_once_with("Title", "")


def test_update_campaign(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "campaign", "update", "c1", "--title", "New Title"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.update_campaign.assert_called_once_with("c1", "New Title", None)


def test_delete_campaign(runner, mock_logger_client):
    result = runner.invoke(main, ["logger", "campaign", "delete", "c1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.delete_campaign.assert_called_once_with("c1")


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
