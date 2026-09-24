import asyncio
import json
import os

import pytest

from campaign_logger.api import GeneratorClient
from campaign_logger.api import LoggerClient
from campaign_logger.mcp_server import create_mcp_server
from campaign_logger.tags import NOTE_TAG_SYMBOL
from campaign_logger.tags import TAG_NAMES
from campaign_logger.tags import TAG_TYPES
from campaign_logger.tags import render_legend


@pytest.fixture
def mock_logger_client(mocker):
    client = mocker.MagicMock(spec=LoggerClient)
    mocker.patch("campaign_logger.mcp_server.LoggerClient", return_value=client)
    return client


@pytest.fixture
def mock_generator_client(mocker):
    client = mocker.MagicMock(spec=GeneratorClient)
    mocker.patch("campaign_logger.mcp_server.GeneratorClient", return_value=client)
    return client


@pytest.fixture
def auth_env(mocker):
    mocker.patch.dict(
        os.environ,
        {"CL_GENERATOR_TOKEN": "test-token", "CL_LOGGER_CLIENT_ID": "test-id", "CL_LOGGER_CLIENT_SECRET": "test-secret"},
        clear=True,
    )
    mocker.patch("campaign_logger.mcp_server.load_config")


def test_list_campaigns(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    # Mock return value
    mock_campaign = mocker.MagicMock()
    mock_campaign.id = "c1"
    mock_campaign.title = "Campaign 1"
    mock_campaign.description = "Desc 1"
    mock_logger_client.get_campaigns.return_value = [mock_campaign]

    server._tool_manager._tools.get("list_campaigns")
    result = asyncio.run(server.call_tool("list_campaigns", {}))
    assert "c1: Campaign 1" in str(result)


def test_get_campaign(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    mock_campaign = mocker.MagicMock()
    mock_campaign.model_dump_json.return_value = '{"id": "c1"}'
    mock_logger_client.get_campaign.return_value = mock_campaign

    result = asyncio.run(server.call_tool("get_campaign", {"campaign_id": "c1"}))
    assert "c1" in str(result)


def test_list_logs(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    mock_log = mocker.MagicMock()
    mock_log.id = "l1"
    mock_log.title = "Log 1"
    mock_log.description = "Desc 1"
    mock_logger_client.get_logs.return_value = [mock_log]

    result = asyncio.run(server.call_tool("list_logs", {}))
    assert "l1: Log 1" in str(result)


def test_get_log(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    mock_log = mocker.MagicMock()
    mock_log.model_dump_json.return_value = '{"id": "l1"}'
    mock_logger_client.get_log.return_value = mock_log

    result = asyncio.run(server.call_tool("get_log", {"log_id": "l1"}))
    assert "l1" in str(result)


def test_list_log_entries(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    mock_entry = mocker.MagicMock()
    mock_entry.id = "e1"
    mock_entry.title = "Entry 1"
    mock_entry.raw_text = "text"
    mock_logger_client.get_log_entries.return_value = [mock_entry]

    result = asyncio.run(server.call_tool("list_log_entries", {}))
    assert "e1: Entry 1" in str(result)


def test_get_log_entry(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    mock_entry = mocker.MagicMock()
    mock_entry.model_dump_json.return_value = '{"id": "e1"}'
    mock_logger_client.get_log_entry.return_value = mock_entry

    result = asyncio.run(server.call_tool("get_log_entry", {"entry_id": "e1"}))
    assert "e1" in str(result)


def test_list_campaign_entries(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    mock_entry = mocker.MagicMock()
    mock_entry.id = "ce1"
    mock_entry.tag_value = "Camp Entry 1"
    mock_entry.raw_text = "text"
    mock_logger_client.get_campaign_entries.return_value = [mock_entry]

    result = asyncio.run(server.call_tool("list_campaign_entries", {}))
    assert "ce1: Camp Entry 1" in str(result)


def test_get_campaign_entry(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    mock_entry = mocker.MagicMock()
    mock_entry.model_dump_json.return_value = '{"id": "ce1"}'
    mock_logger_client.get_campaign_entry.return_value = mock_entry

    result = asyncio.run(server.call_tool("get_campaign_entry", {"entry_id": "ce1"}))
    assert "ce1" in str(result)


def test_list_generators(mock_generator_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    mock_gen = mocker.MagicMock()
    mock_gen.id = "g1"
    mock_gen.name = "Gen 1"
    mock_generator_client.list_generators.return_value = [mock_gen]

    result = asyncio.run(server.call_tool("list_generators", {}))
    assert "g1: Gen 1" in str(result)


def test_get_generator(mock_generator_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    mock_gen = mocker.MagicMock()
    mock_gen.model_dump_json.return_value = '{"id": "g1"}'
    mock_generator_client.get_generator.return_value = mock_gen

    result = asyncio.run(server.call_tool("get_generator", {"generator_id": "g1"}))
    assert "g1" in str(result)


def test_get_generator_by_name_fallback(mock_generator_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    mock_generator_client.get_generator.side_effect = Exception("Not found")
    mock_gen = mocker.MagicMock()
    mock_gen.model_dump_json.return_value = '{"id": "g1"}'
    mock_generator_client.get_generator_by_name.return_value = mock_gen

    result = asyncio.run(server.call_tool("get_generator", {"generator_id": "g1"}))
    assert "g1" in str(result)


def test_get_generator_not_found(mock_generator_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    mock_generator_client.get_generator.side_effect = Exception("Not found")
    mock_generator_client.get_generator_by_name.return_value = None

    with pytest.raises(Exception, match="Generator not found"):
        asyncio.run(server.call_tool("get_generator", {"generator_id": "g1"}))


def test_generate_result(mock_generator_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    mock_generator_client.execute_operation.return_value = {"result": "success"}

    result = asyncio.run(server.call_tool("generate_result", {"target": "g1"}))
    assert "success" in str(result)


def test_generate_result_fallback(mock_generator_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    mock_generator_client.execute_operation.side_effect = [Exception("Not found"), {"result": "success"}]
    mock_gen = mocker.MagicMock()
    mock_gen.id = "g1"
    mock_generator_client.get_generator_by_name.return_value = mock_gen

    result = asyncio.run(server.call_tool("generate_result", {"target": "g1"}))
    assert "success" in str(result)


def test_generate_result_not_found(mock_generator_client, auth_env, mocker):
    server = create_mcp_server(read_only=True)

    mock_generator_client.execute_operation.side_effect = Exception("Not found")
    mock_generator_client.get_generator_by_name.return_value = None

    with pytest.raises(Exception, match="Generator not found"):
        asyncio.run(server.call_tool("generate_result", {"target": "g1"}))


# Write tools
def test_create_campaign(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=False)

    mock_campaign = mocker.MagicMock()
    mock_campaign.model_dump_json.return_value = '{"id": "c1"}'
    mock_logger_client.create_campaign.return_value = mock_campaign

    result = asyncio.run(server.call_tool("create_campaign", {"title": "C1"}))
    assert "c1" in str(result)


def test_update_campaign(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=False)

    mock_campaign = mocker.MagicMock()
    mock_campaign.model_dump_json.return_value = '{"id": "c1"}'
    mock_logger_client.update_campaign.return_value = mock_campaign

    result = asyncio.run(server.call_tool("update_campaign", {"campaign_id": "c1"}))
    assert "c1" in str(result)


def test_delete_campaign(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=False)

    result = asyncio.run(server.call_tool("delete_campaign", {"campaign_id": "c1"}))
    assert "deleted" in str(result).lower()


def test_create_log(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=False)

    mock_log = mocker.MagicMock()
    mock_log.model_dump_json.return_value = '{"id": "l1"}'
    mock_logger_client.create_log.return_value = mock_log

    result = asyncio.run(server.call_tool("create_log", {"campaign_id": "c1", "title": "L1"}))
    assert "l1" in str(result)


def test_update_log(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=False)

    mock_log = mocker.MagicMock()
    mock_log.model_dump_json.return_value = '{"id": "l1"}'
    mock_logger_client.update_log.return_value = mock_log

    result = asyncio.run(server.call_tool("update_log", {"log_id": "l1"}))
    assert "l1" in str(result)


def test_delete_log(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=False)

    result = asyncio.run(server.call_tool("delete_log", {"log_id": "l1"}))
    assert "deleted" in str(result).lower()


def test_create_log_entry(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=False)

    mock_entry = mocker.MagicMock()
    mock_entry.model_dump_json.return_value = '{"id": "e1"}'
    mock_logger_client.create_log_entry.return_value = mock_entry

    result = asyncio.run(server.call_tool("create_log_entry", {"log_id": "l1", "text": "T1"}))
    assert "e1" in str(result)


def test_update_log_entry(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=False)

    mock_entry = mocker.MagicMock()
    mock_entry.model_dump_json.return_value = '{"id": "e1"}'
    mock_logger_client.update_log_entry.return_value = mock_entry

    result = asyncio.run(server.call_tool("update_log_entry", {"entry_id": "e1", "text": "T2"}))
    assert "e1" in str(result)


def test_delete_log_entry(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=False)

    result = asyncio.run(server.call_tool("delete_log_entry", {"entry_id": "e1"}))
    assert "deleted" in str(result).lower()


def test_create_campaign_entry(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=False)

    mock_entry = mocker.MagicMock()
    mock_entry.model_dump_json.return_value = '{"id": "ce1"}'
    mock_logger_client.create_campaign_entry.return_value = mock_entry

    result = asyncio.run(server.call_tool("create_campaign_entry", {"campaign_id": "c1", "text": "T1"}))
    assert "ce1" in str(result)


def test_update_campaign_entry(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=False)

    mock_entry = mocker.MagicMock()
    mock_entry.model_dump_json.return_value = '{"id": "ce1"}'
    mock_logger_client.update_campaign_entry.return_value = mock_entry

    result = asyncio.run(server.call_tool("update_campaign_entry", {"entry_id": "ce1", "text": "T2"}))
    assert "ce1" in str(result)


def test_delete_campaign_entry(mock_logger_client, auth_env, mocker):
    server = create_mcp_server(read_only=False)

    result = asyncio.run(server.call_tool("delete_campaign_entry", {"entry_id": "ce1"}))
    assert "deleted" in str(result).lower()


# --- get_tag_types: the one tool that needs no credentials (#87, #97) ---------


@pytest.fixture
def no_auth_env(mocker):
    """No credentials at all, and no config file to supply any."""
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch("campaign_logger.mcp_server.load_config")


def call_tag_types(server, arguments=None):
    """Invoke ``get_tag_types`` and parse its JSON payload."""
    result = asyncio.run(server.call_tool("get_tag_types", arguments or {}))
    return json.loads(result.content[0].text)


def test_get_tag_types_needs_no_credentials(no_auth_env):
    """The table is static, so this must answer where every other tool raises.

    Asserted against a server built with an empty environment: if the tool ever
    acquires a ``require_logger``/``require_generator`` wrapper, this fails.
    """
    payload = call_tag_types(create_mcp_server(read_only=True))
    assert payload["tag-types"]


@pytest.mark.parametrize("read_only", [True, False])
def test_get_tag_types_registered_in_both_modes(no_auth_env, read_only):
    """Reading the type system is not a write, so --write must not be required."""
    server = create_mcp_server(read_only=read_only)
    assert "get_tag_types" in server._tool_manager._tools


def test_get_tag_types_covers_every_symbol(no_auth_env):
    """Every symbol in TAG_TYPES is reported, with its label and short name."""
    payload = call_tag_types(create_mcp_server(read_only=True))

    reported = {entry["symbol"]: entry for entry in payload["tag-types"]}
    assert reported.keys() == TAG_TYPES.keys()
    for symbol, label in TAG_TYPES.items():
        assert reported[symbol]["label"] == label
        assert reported[symbol]["name"] == TAG_NAMES[symbol]


def test_get_tag_types_reports_the_legend_and_note_symbol(no_auth_env):
    """The rendered legend is served as-is rather than re-derived by the caller."""
    payload = call_tag_types(create_mcp_server(read_only=True))
    assert payload["legend"] == render_legend()
    assert payload["note-symbol"] == NOTE_TAG_SYMBOL


def test_get_tag_types_accepts_a_campaign_and_says_it_did_not_apply_it(no_auth_env):
    """The campaign argument is recorded, never silently treated as honoured.

    This is the contract that keeps #97 visible: a caller passing a campaign must
    be able to tell from the response that the answer is not campaign-scoped,
    rather than having to know. When #97 lands, this assertion is what should
    change -- deliberately, not by accident.
    """
    payload = call_tag_types(create_mcp_server(read_only=True), {"campaign": "Steel and Chaos"})

    assert payload["campaign-requested"] == "Steel and Chaos"
    assert payload["campaign-applied"] is None
    assert payload["scope"] == "campaign-logger-defaults"
    assert "#97" in payload["campaign-scoping"]


def test_get_tag_types_campaign_is_optional(no_auth_env):
    """Omitting the campaign is valid and reports no campaign requested."""
    payload = call_tag_types(create_mcp_server(read_only=True))
    assert payload["campaign-requested"] is None
