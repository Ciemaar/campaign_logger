from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from campaign_logger.cli import main
from campaign_logger.models import Campaign
from campaign_logger.models import CampaignEntry
from campaign_logger.models import Log
from campaign_logger.models import LogEntry
from campaign_logger.models import PlayerLog
from campaign_logger.models import PlayerLogEntry


@pytest.fixture
def runner():
    return CliRunner()


def bind(entity, client):
    """Attach ``client`` to a real model so its ``save()`` can round-trip.

    The models reach their client through the ``_client`` private attribute, so a
    model built directly in a test has to be given one before the CLI's
    ``obj.save().to_dict()`` path will work.
    """
    entity._client = client
    return entity


@pytest.fixture
def mock_logger_client(mocker):
    """A mocked client returning **real models**, not mock stubs.

    These were ``MagicMock`` subclasses, which meant the CLI tests never
    exercised a single real model: any attribute returned a mock, so every
    ``exit_code == 0`` assertion passed regardless of what the CLI actually read
    off the object. That is how #89 shipped -- `page get` read `raw_text`
    directly and printed nothing for a page whose body is only in `raw_public`,
    and no test noticed because the mock answered `raw_text` too. Using real
    models makes the CLI's reads real (#95).
    """
    mock_instance = MagicMock()
    mock_c1 = bind(Campaign(id="c1", type="campaigns", title="Camp Title"), mock_instance)
    mock_l1 = bind(Log(id="l1", type="logs", title="Log Title"), mock_instance)
    mock_le1 = bind(LogEntry(id="le1", type="log-entries", raw_text="Text 1"), mock_instance)
    mock_ce1 = bind(CampaignEntry(id="ce1", type="campaign-entries", raw_text="Page 1"), mock_instance)

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

    mock_pl1 = bind(PlayerLog(id="pl1", type="player-logs", title="Player Log Title"), mock_instance)
    mock_ple1 = bind(PlayerLogEntry(id="ple1", type="player-log-entries", raw_text="Player Text 1"), mock_instance)

    mock_instance.get_player_logs.return_value = [mock_pl1]
    mock_instance.get_player_log.return_value = mock_pl1
    mock_instance.create_player_log.return_value = mock_pl1
    mock_instance.update_player_log.return_value = mock_pl1

    mock_instance.get_player_log_entries.return_value = [mock_ple1]
    mock_instance.get_player_log_entry.return_value = mock_ple1
    mock_instance.create_player_log_entry.return_value = mock_ple1
    mock_instance.update_player_log_entry.return_value = mock_ple1

    mocker.patch("campaign_logger.cli.LoggerClient", return_value=mock_instance)
    return mock_instance


def test_list_campaigns(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "campaign", "list"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_campaigns.assert_called_once()


def test_create_campaign(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "campaign", "create", "Title"])
    assert result.exit_code == 0  # nosec
    assert '"c1"' in result.output  # nosec
    mock_logger_client.create_campaign.assert_called_once_with("Title", "")


def test_update_campaign(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "campaign", "update", "c1", "--title", "New Title", "--description", "Desc"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_campaign.assert_called_once_with("c1")


def test_update_log(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "log", "update", "l1", "--title", "New Title", "--description", "Desc"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_log.assert_called_with("l1")


def test_update_entry(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "entry", "update", "le1", "text"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_log_entry.assert_called_with("le1")


def test_update_page(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "page", "update", "ce1", "text"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_campaign_entry.assert_called_with("ce1")


def test_delete_campaign(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "campaign", "delete", "c1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.delete_campaign.assert_called_once_with("c1")


def test_list_player_logs(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "player-log", "list"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_player_logs.assert_called_once()


def test_get_player_log(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "player-log", "get", "pl1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_player_log.assert_called_once_with("pl1")


def test_create_player_log(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "player-log", "create", "c1", "Title"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.create_player_log.assert_called_once_with("c1", "Title", "")


def test_update_player_log(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "player-log", "update", "pl1", "--title", "New"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_player_log.assert_called_once_with("pl1")


def test_delete_player_log(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "player-log", "delete", "pl1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.delete_player_log.assert_called_once_with("pl1")


def test_list_player_entries(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "player-entry", "list"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_player_log_entries.assert_called_once()


def test_get_player_entry(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "player-entry", "get", "ple1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_player_log_entry.assert_called_once_with("ple1")


def test_create_player_entry(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "player-entry", "create", "pl1", "text"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.create_player_log_entry.assert_called_once_with("pl1", "text")


def test_update_player_entry(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "player-entry", "update", "ple1", "new text"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_player_log_entry.assert_called_once_with("ple1")


def test_delete_player_entry(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "player-entry", "delete", "ple1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.delete_player_log_entry.assert_called_once_with("ple1")


def test_list_logs(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "log", "list"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_logs.assert_called_once()


def test_get_log(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "log", "get", "l1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_log.assert_called_once_with("l1")


def test_delete_log(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "log", "delete", "l1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.delete_log.assert_called_once_with("l1")


def test_list_entries(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "entry", "list"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_log_entries.assert_called_once()


def test_get_entry(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "entry", "get", "le1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_log_entry.assert_called_once_with("le1")


def test_delete_entry(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "entry", "delete", "le1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.delete_log_entry.assert_called_once_with("le1")


def test_list_pages(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "page", "list"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_campaign_entries.assert_called_once()


def test_get_page(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "page", "get", "ce1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.get_campaign_entry.assert_called_once_with("ce1")


def test_delete_page(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "page", "delete", "ce1"])
    assert result.exit_code == 0  # nosec
    mock_logger_client.delete_campaign_entry.assert_called_once_with("ce1")


def test_create_log(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "log", "create", "c1", "Log Title"])
    assert result.exit_code == 0  # nosec
    assert '"l1"' in result.output  # nosec
    mock_logger_client.create_log.assert_called_once_with("c1", "Log Title", "")


def test_create_entry(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "entry", "create", "l1", "text"])
    assert result.exit_code == 0  # nosec
    assert '"le1"' in result.output  # nosec
    mock_logger_client.create_log_entry.assert_called_once_with("l1", "text")


def test_create_page(runner, mock_logger_client, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "page", "create", "c1", "text"])
    assert result.exit_code == 0  # nosec
    assert '"ce1"' in result.output  # nosec
    mock_logger_client.create_campaign_entry.assert_called_once_with("c1", "text")


def test_logger_cli_error_handling(runner, mock_logger_client, monkeypatch):

    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")

    mock_logger_client.get_campaigns.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "campaign", "list"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_campaign.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "campaign", "get", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.create_campaign.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "campaign", "create", "title"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_campaign.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "campaign", "update", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.delete_campaign.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "campaign", "delete", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_player_logs.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "player-log", "list"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_player_log.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "player-log", "get", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.create_player_log.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "player-log", "create", "1", "title"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_player_log.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "player-log", "update", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.delete_player_log.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "player-log", "delete", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_player_log_entries.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "player-entry", "list"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_player_log_entry.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "player-entry", "get", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.create_player_log_entry.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "player-entry", "create", "1", "text"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_player_log_entry.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "player-entry", "update", "1", "text"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.delete_player_log_entry.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "player-entry", "delete", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_logs.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "log", "list"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_log.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "log", "get", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.create_log.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "log", "create", "1", "title"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_log.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "log", "update", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.delete_log.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "log", "delete", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_log_entries.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "entry", "list"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_log_entry.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "entry", "get", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.create_log_entry.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "entry", "create", "1", "text"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_log_entry.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "entry", "update", "1", "text"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.delete_log_entry.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "entry", "delete", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_campaign_entries.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "page", "list"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_campaign_entry.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "page", "get", "1"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.create_campaign_entry.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "page", "create", "1", "text"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.get_campaign_entry.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "page", "update", "1", "text"])
    assert "Error: API error" in result.output  # nosec

    mock_logger_client.delete_campaign_entry.side_effect = OSError("API error")
    result = runner.invoke(main, ["logger", "page", "delete", "1"])
    assert "Error: API error" in result.output  # nosec


def test_campaign_get_outputs_valid_json_with_real_model(runner, mocker, monkeypatch):
    """The CLI's json.dumps(to_dict()) must work on a REAL model, not a MagicMock.

    Every other CLI test substitutes MockResource, which carries its own
    to_dict(), so the real model's serialisation is never exercised. That gap let
    the datetime fields (#44) break `campaign get` against real data without a
    single test failing. This test drives the genuine parser and model.
    """
    import json as _json

    from wire import realistic_campaign

    from campaign_logger.api import LoggerClient

    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")

    real_campaign = LoggerClient()._parse_campaign(realistic_campaign())
    instance = MagicMock()
    instance.get_campaign.return_value = real_campaign
    mocker.patch("campaign_logger.cli.LoggerClient", return_value=instance)

    result = runner.invoke(main, ["logger", "campaign", "get", "c1"])

    assert result.exit_code == 0, result.output  # nosec
    payload = _json.loads(result.output)  # would raise if to_dict() were not JSON-safe
    assert payload["id"] == "c1"  # nosec
    assert payload["created_on"] == "2026-09-16T02:26:10.416000"  # nosec
    assert payload["revision"] == "7ac376fe32bf42d6862f05743f75231b"  # nosec
