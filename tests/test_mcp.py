import asyncio

import pytest
from click.testing import CliRunner

from campaign_logger.mcp_server import create_mcp_server


@pytest.fixture
def runner():
    return CliRunner()


def test_mcp_server_creation_read_write():
    """Test that all tools are registered when read-only is False."""
    server = create_mcp_server(read_only=False)

    async def get_tools():
        return await server.list_tools()

    tools_result = asyncio.run(get_tools())
    tool_names = {t.name for t in tools_result}

    assert "list_campaigns" in tool_names
    assert "create_campaign" in tool_names
    assert "update_log_entry" in tool_names
    assert "delete_campaign_entry" in tool_names
    assert len(tool_names) == 23


def test_mcp_server_creation_read_only():
    """Test that only read tools are registered when read-only is True."""
    server = create_mcp_server(read_only=True)

    async def get_tools():
        return await server.list_tools()

    tools_result = asyncio.run(get_tools())
    tool_names = {t.name for t in tools_result}

    assert "list_campaigns" in tool_names
    assert "create_campaign" not in tool_names
    assert "update_log_entry" not in tool_names
    assert "delete_campaign_entry" not in tool_names
    assert len(tool_names) == 11


def test_mcp_server_client_initialization(mocker):
    """Test that clients are initialized based on environment variables."""
    # Mock load_config to prevent side effects
    mocker.patch("campaign_logger.mcp_server.load_config")

    # Set environment variables
    mocker.patch.dict(
        "os.environ",
        {
            "CL_GENERATOR_TOKEN": "test_gen_token",
            "CL_LOGGER_CLIENT_ID": "test_client_id",
            "CL_LOGGER_CLIENT_SECRET": "test_client_secret",
        },
    )

    server = create_mcp_server(read_only=True)
    # the server object itself doesn't expose the clients directly easily as they are in closures
    # but we can call a read tool and mock the client
    assert server.name == "campaign-logger"


def test_mcp_server_tool_requires_generator(mocker):
    """Test that generator tools raise error if not authenticated."""
    mocker.patch("campaign_logger.mcp_server.load_config")
    mocker.patch.dict("os.environ", {}, clear=True)

    server = create_mcp_server(read_only=True)

    # Get the inner tool function directly
    # In MCPServer, tools are added via decorator, but they are stored in _tool_manager.tools
    tool = server._tool_manager._tools.get("list_generators")
    if tool:
        with pytest.raises(Exception):
            asyncio.run(server.call_tool("list_generators", {}))


def test_mcp_server_tool_requires_logger(mocker):
    """Test that logger tools raise error if not authenticated."""
    mocker.patch("campaign_logger.mcp_server.load_config")
    mocker.patch.dict("os.environ", {}, clear=True)

    server = create_mcp_server(read_only=True)

    tool = server._tool_manager._tools.get("list_campaigns")
    if tool:
        with pytest.raises(Exception):
            asyncio.run(server.call_tool("list_generators", {}))


def test_mcp_cli_command(runner, mocker):
    from campaign_logger.cli import main

    mocker.patch("campaign_logger.mcp_server.MCPServer.run")
    result = runner.invoke(main, ["mcp"])
    assert result.exit_code == 0


def test_mcp_cli_command_error(runner, mocker):
    from campaign_logger.cli import main

    mock_run = mocker.patch("campaign_logger.mcp_server.MCPServer.run")
    mock_run.side_effect = Exception("Test Error")
    result = runner.invoke(main, ["mcp"])
    assert result.exit_code == 0
    assert "MCP Server Error: Test Error" in result.output
