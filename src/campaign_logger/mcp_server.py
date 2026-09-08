"""MCP server integration for Campaign Logger."""

import functools
import json
import os
import typing

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from .api import GeneratorClient
from .api import LoggerClient
from .cli import load_config


def create_mcp_server(read_only: bool = True) -> MCPServer:
    """Create and configure the Campaign Logger MCP server."""
    server = MCPServer("campaign-logger")

    load_config()

    generator_token = os.environ.get("CL_GENERATOR_TOKEN")
    logger_client_id = os.environ.get("CL_LOGGER_CLIENT_ID")
    logger_client_secret = os.environ.get("CL_LOGGER_CLIENT_SECRET")

    generator_client = None
    if generator_token:
        generator_client = GeneratorClient(token=generator_token)

    logger_client = None
    if logger_client_id and logger_client_secret:
        logger_client = LoggerClient(client_id=logger_client_id, client_secret=logger_client_secret)

    def require_logger(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not logger_client:
                raise ToolError("Logger client not authenticated. Set CL_LOGGER_CLIENT_ID and CL_LOGGER_CLIENT_SECRET.")
            kwargs["client"] = logger_client
            return func(*args, **kwargs)

        return wrapper

    def require_generator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not generator_client:
                raise ToolError("Generator client not authenticated. Set CL_GENERATOR_TOKEN.")
            kwargs["client"] = generator_client
            return func(*args, **kwargs)

        return wrapper

    # --- Read Tools ---

    @server.tool()
    @require_logger
    def list_campaigns(client: typing.Any = Field(default=None, exclude=True)) -> str:
        """Retrieve a list of all campaigns available to the user."""
        campaigns = client.get_campaigns()
        return "\n".join(f"{c.id}: {c.title}" for c in campaigns) if campaigns else "No campaigns found."

    @server.tool()
    @require_logger
    def get_campaign(
        campaign_id: str = Field(..., description="The ID of the campaign to retrieve"),
        client: typing.Any = Field(default=None, exclude=True),
    ) -> str:
        """Fetch the full details of a specific campaign by its ID."""
        campaign = client.get_campaign(campaign_id)
        return campaign.model_dump_json(indent=2)

    @server.tool()
    @require_logger
    def list_logs(client: typing.Any = Field(default=None, exclude=True)) -> str:
        """Retrieve a list of all logs available across the user's campaigns."""
        logs = client.get_logs()
        return "\n".join(f"{log.id}: {log.title}" for log in logs) if logs else "No logs found."

    @server.tool()
    @require_logger
    def get_log(
        log_id: str = Field(..., description="The ID of the log to retrieve"),
        client: typing.Any = Field(default=None, exclude=True),
    ) -> str:
        """Fetch the full details of a specific log by its ID."""
        log = client.get_log(log_id)
        return log.model_dump_json(indent=2)

    @server.tool()
    @require_logger
    def list_log_entries(
        log_id: str | None = Field(None, description="Optional log ID to filter the entries"),
        client: typing.Any = Field(default=None, exclude=True),
    ) -> str:
        """Retrieve all individual log entries, optionally filtering by a specific log ID."""
        entries = client.get_log_entries(log_id=log_id)
        result = []
        for e in entries:
            text = e.raw_text.strip() if getattr(e, "raw_text", None) else ""
            title = getattr(e, "title", "")
            if not title and text:
                title = text.splitlines()[0]
            if not title:
                continue
            result.append(f"{e.id}: {title}")
        return "\n".join(result) if result else "No log entries found."

    @server.tool()
    @require_logger
    def get_log_entry(
        entry_id: str = Field(..., description="The ID of the log entry to retrieve"),
        client: typing.Any = Field(default=None, exclude=True),
    ) -> str:
        """Fetch the full details of a specific log entry by its ID."""
        entry = client.get_log_entry(entry_id)
        return entry.model_dump_json(indent=2)

    @server.tool()
    @require_logger
    def list_campaign_entries(
        campaign_id: str | None = Field(None, description="Optional campaign ID to filter the pages"),
        client: typing.Any = Field(default=None, exclude=True),
    ) -> str:
        """Retrieve all top-level campaign pages, optionally filtering by campaign ID."""
        entries = client.get_campaign_entries(campaign_id=campaign_id)
        result = []
        for p in entries:
            text = p.raw_text.strip() if getattr(p, "raw_text", None) else ""
            title = getattr(p, "tag_value", "")
            if not title and text:
                title = text.splitlines()[0]
            if not title:
                continue
            result.append(f"{p.id}: {title}")
        return "\n".join(result) if result else "No campaign entries (pages) found."

    @server.tool()
    @require_logger
    def get_campaign_entry(
        entry_id: str = Field(..., description="The ID of the campaign entry (page) to retrieve"),
        client: typing.Any = Field(default=None, exclude=True),
    ) -> str:
        """Fetch the full details of a specific campaign entry (page) by its ID."""
        entry = client.get_campaign_entry(entry_id)
        return entry.model_dump_json(indent=2)

    @server.tool()
    @require_generator
    def list_generators(client: typing.Any = Field(default=None, exclude=True)) -> str:
        """Retrieve a list of all generators available to the user."""
        generators = client.list_generators()
        return "\n".join(f"{g.id}: {g.name}" for g in generators) if generators else "No generators found."

    @server.tool()
    @require_generator
    def get_generator(
        generator_id: str = Field(..., description="The ID or Name of the generator to retrieve"),
        client: typing.Any = Field(default=None, exclude=True),
    ) -> str:
        """Fetch the configuration of a specific generator by its ID or Name."""
        try:
            generator = client.get_generator(generator_id)
        except Exception:
            generator = client.get_generator_by_name(generator_id)
            if not generator:
                raise ToolError("Generator not found by ID or Name")
        return generator.model_dump_json(indent=2)

    @server.tool()
    @require_generator
    def generate_result(
        target: str = Field(..., description="The generator ID or Name to generate a result from"),
        client: typing.Any = Field(default=None, exclude=True),
    ) -> str:
        """Generate a random outcome from a generator."""
        try:
            result = client.execute_operation(target, "generate")
        except Exception:
            gen = client.get_generator_by_name(target)
            if gen and gen.id:
                result = client.execute_operation(gen.id, "generate")
            else:
                raise ToolError("Generator not found by ID or Name")

        return json.dumps(result, indent=2, sort_keys=True)

    # --- Write Tools (Conditional) ---
    if not read_only:

        @server.tool()
        @require_logger
        def create_campaign(
            title: str = Field(..., description="The title of the new campaign"),
            description: str = Field("", description="The description of the new campaign"),
            client: typing.Any = Field(default=None, exclude=True),
        ) -> str:
            """Create a new top-level campaign."""
            campaign = client.create_campaign(title, description)
            return f"Campaign created successfully:\n{campaign.model_dump_json(indent=2)}"

        @server.tool()
        @require_logger
        def update_campaign(
            campaign_id: str = Field(..., description="The ID of the campaign to update"),
            title: str | None = Field(None, description="New title for the campaign"),
            description: str | None = Field(None, description="New description for the campaign"),
            client: typing.Any = Field(default=None, exclude=True),
        ) -> str:
            """Modify the metadata attributes (title/description) of a campaign."""
            campaign = client.update_campaign(campaign_id, title=title, description=description)
            return f"Campaign updated successfully:\n{campaign.model_dump_json(indent=2)}"

        @server.tool()
        @require_logger
        def delete_campaign(
            campaign_id: str = Field(..., description="The ID of the campaign to delete"),
            client: typing.Any = Field(default=None, exclude=True),
        ) -> str:
            """Permanently delete a campaign and its associated contents."""
            client.delete_campaign(campaign_id)
            return f"Campaign {campaign_id} deleted successfully."

        @server.tool()
        @require_logger
        def create_log(
            campaign_id: str = Field(..., description="The ID of the campaign to attach the log to"),
            title: str = Field(..., description="The title of the new log"),
            description: str = Field("", description="The description of the new log"),
            client: typing.Any = Field(default=None, exclude=True),
        ) -> str:
            """Create a new child log attached to a specific campaign."""
            log = client.create_log(campaign_id, title, description)
            return f"Log created successfully:\n{log.model_dump_json(indent=2)}"

        @server.tool()
        @require_logger
        def update_log(
            log_id: str = Field(..., description="The ID of the log to update"),
            title: str | None = Field(None, description="New title for the log"),
            description: str | None = Field(None, description="New description for the log"),
            client: typing.Any = Field(default=None, exclude=True),
        ) -> str:
            """Modify the metadata attributes (title/description) of a log."""
            log = client.update_log(log_id, title=title, description=description)
            return f"Log updated successfully:\n{log.model_dump_json(indent=2)}"

        @server.tool()
        @require_logger
        def delete_log(
            log_id: str = Field(..., description="The ID of the log to delete"),
            client: typing.Any = Field(default=None, exclude=True),
        ) -> str:
            """Permanently delete a log and its associated entries."""
            client.delete_log(log_id)
            return f"Log {log_id} deleted successfully."

        @server.tool()
        @require_logger
        def create_log_entry(
            log_id: str = Field(..., description="The ID of the log to attach the entry to"),
            text: str = Field(..., description="The text content of the new log entry"),
            client: typing.Any = Field(default=None, exclude=True),
        ) -> str:
            """Append a new text entry to a specific log."""
            entry = client.create_log_entry(log_id, text)
            return f"Log entry created successfully:\n{entry.model_dump_json(indent=2)}"

        @server.tool()
        @require_logger
        def update_log_entry(
            entry_id: str = Field(..., description="The ID of the log entry to update"),
            text: str = Field(..., description="The new text content of the log entry"),
            client: typing.Any = Field(default=None, exclude=True),
        ) -> str:
            """Modify the text content of a specific log entry."""
            entry = client.update_log_entry(entry_id, text)
            return f"Log entry updated successfully:\n{entry.model_dump_json(indent=2)}"

        @server.tool()
        @require_logger
        def delete_log_entry(
            entry_id: str = Field(..., description="The ID of the log entry to delete"),
            client: typing.Any = Field(default=None, exclude=True),
        ) -> str:
            """Permanently delete a log entry."""
            client.delete_log_entry(entry_id)
            return f"Log entry {entry_id} deleted successfully."

        @server.tool()
        @require_logger
        def create_campaign_entry(
            campaign_id: str = Field(..., description="The ID of the campaign to attach the page to"),
            text: str = Field(..., description="The text content of the new campaign page"),
            client: typing.Any = Field(default=None, exclude=True),
        ) -> str:
            """Create a new top-level page (Campaign Entry) attached to a specific campaign."""
            entry = client.create_campaign_entry(campaign_id, text)
            return f"Campaign entry (page) created successfully:\n{entry.model_dump_json(indent=2)}"

        @server.tool()
        @require_logger
        def update_campaign_entry(
            entry_id: str = Field(..., description="The ID of the campaign entry (page) to update"),
            text: str = Field(..., description="The new text content of the campaign page"),
            client: typing.Any = Field(default=None, exclude=True),
        ) -> str:
            """Modify the text content of a specific campaign page."""
            entry = client.update_campaign_entry(entry_id, text)
            return f"Campaign entry (page) updated successfully:\n{entry.model_dump_json(indent=2)}"

        @server.tool()
        @require_logger
        def delete_campaign_entry(
            entry_id: str = Field(..., description="The ID of the campaign entry (page) to delete"),
            client: typing.Any = Field(default=None, exclude=True),
        ) -> str:
            """Permanently delete a campaign page."""
            client.delete_campaign_entry(entry_id)
            return f"Campaign entry (page) {entry_id} deleted successfully."

    return server


def run_mcp_server(read_only: bool = True) -> None:
    """Run the Campaign Logger MCP server."""
    server = create_mcp_server(read_only=read_only)
    server.run()
