"""MCP server integration for Campaign Logger."""

import json
import os

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from .api import GeneratorClient
from .api import LoggerClient
from .cli import load_config


def create_mcp_server(read_only: bool = False) -> MCPServer:
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

    def _require_logger():
        if not logger_client:
            raise Exception("Logger client not authenticated. Set CL_LOGGER_CLIENT_ID and CL_LOGGER_CLIENT_SECRET.")
        return logger_client

    def _require_generator():
        if not generator_client:
            raise Exception("Generator client not authenticated. Set CL_GENERATOR_TOKEN.")
        return generator_client

    # --- Read Tools ---

    @server.tool()
    def list_campaigns() -> str:
        """Retrieve a list of all campaigns available to the user."""
        client = _require_logger()
        campaigns = client.get_campaigns()
        return "\n".join(f"{c.id}: {c.title}" for c in campaigns) if campaigns else "No campaigns found."

    @server.tool()
    def get_campaign(
        campaign_id: str = Field(..., description="The ID of the campaign to retrieve"),
    ) -> str:
        """Fetch the full details of a specific campaign by its ID."""
        client = _require_logger()
        campaign = client.get_campaign(campaign_id)
        return campaign.model_dump_json(indent=2)

    @server.tool()
    def list_logs() -> str:
        """Retrieve a list of all logs available across the user's campaigns."""
        client = _require_logger()
        logs = client.get_logs()
        return "\n".join(f"{log.id}: {log.title}" for log in logs) if logs else "No logs found."

    @server.tool()
    def get_log(
        log_id: str = Field(..., description="The ID of the log to retrieve"),
    ) -> str:
        """Fetch the full details of a specific log by its ID."""
        client = _require_logger()
        log = client.get_log(log_id)
        return log.model_dump_json(indent=2)

    @server.tool()
    def list_log_entries(
        log_id: str | None = Field(None, description="Optional log ID to filter the entries"),
    ) -> str:
        """Retrieve all individual log entries, optionally filtering by a specific log ID."""
        client = _require_logger()
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
    def get_log_entry(
        entry_id: str = Field(..., description="The ID of the log entry to retrieve"),
    ) -> str:
        """Fetch the full details of a specific log entry by its ID."""
        client = _require_logger()
        entry = client.get_log_entry(entry_id)
        return entry.model_dump_json(indent=2)

    @server.tool()
    def list_campaign_entries(
        campaign_id: str | None = Field(None, description="Optional campaign ID to filter the pages"),
    ) -> str:
        """Retrieve all top-level campaign pages, optionally filtering by campaign ID."""
        client = _require_logger()
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
    def get_campaign_entry(
        entry_id: str = Field(..., description="The ID of the campaign entry (page) to retrieve"),
    ) -> str:
        """Fetch the full details of a specific campaign entry (page) by its ID."""
        client = _require_logger()
        entry = client.get_campaign_entry(entry_id)
        return entry.model_dump_json(indent=2)

    @server.tool()
    def list_generators() -> str:
        """Retrieve a list of all generators available to the user."""
        client = _require_generator()
        generators = client.list_generators()
        return "\n".join(f"{g.id}: {g.name}" for g in generators) if generators else "No generators found."

    @server.tool()
    def get_generator(
        generator_id: str = Field(..., description="The ID or Name of the generator to retrieve"),
    ) -> str:
        """Fetch the configuration of a specific generator by its ID or Name."""
        client = _require_generator()
        try:
            generator = client.get_generator(generator_id)
        except Exception:
            generator = client.get_generator_by_name(generator_id)
            if not generator:
                raise ValueError("Generator not found by ID or Name")
        return generator.model_dump_json(indent=2)

    @server.tool()
    def generate_result(
        target: str = Field(..., description="The generator ID or Name to generate a result from"),
    ) -> str:
        """Generate a random outcome from a generator."""
        client = _require_generator()
        try:
            result = client.execute_operation(target, "generate")
        except Exception:
            gen = client.get_generator_by_name(target)
            if gen and gen.id:
                result = client.execute_operation(gen.id, "generate")
            else:
                raise ValueError("Generator not found by ID or Name")

        return json.dumps(result, indent=2)

    # --- Write Tools (Conditional) ---
    if not read_only:

        @server.tool()
        def create_campaign(
            title: str = Field(..., description="The title of the new campaign"),
            description: str = Field("", description="The description of the new campaign"),
        ) -> str:
            """Create a new top-level campaign."""
            client = _require_logger()
            campaign = client.create_campaign(title, description)
            return f"Campaign created successfully:\n{campaign.model_dump_json(indent=2)}"

        @server.tool()
        def update_campaign(
            campaign_id: str = Field(..., description="The ID of the campaign to update"),
            title: str | None = Field(None, description="New title for the campaign"),
            description: str | None = Field(None, description="New description for the campaign"),
        ) -> str:
            """Modify the metadata attributes (title/description) of a campaign."""
            client = _require_logger()
            campaign = client.update_campaign(campaign_id, title=title, description=description)
            return f"Campaign updated successfully:\n{campaign.model_dump_json(indent=2)}"

        @server.tool()
        def delete_campaign(
            campaign_id: str = Field(..., description="The ID of the campaign to delete"),
        ) -> str:
            """Permanently delete a campaign and its associated contents."""
            client = _require_logger()
            client.delete_campaign(campaign_id)
            return f"Campaign {campaign_id} deleted successfully."

        @server.tool()
        def create_log(
            campaign_id: str = Field(..., description="The ID of the campaign to attach the log to"),
            title: str = Field(..., description="The title of the new log"),
            description: str = Field("", description="The description of the new log"),
        ) -> str:
            """Create a new child log attached to a specific campaign."""
            client = _require_logger()
            log = client.create_log(campaign_id, title, description)
            return f"Log created successfully:\n{log.model_dump_json(indent=2)}"

        @server.tool()
        def update_log(
            log_id: str = Field(..., description="The ID of the log to update"),
            title: str | None = Field(None, description="New title for the log"),
            description: str | None = Field(None, description="New description for the log"),
        ) -> str:
            """Modify the metadata attributes (title/description) of a log."""
            client = _require_logger()
            log = client.update_log(log_id, title=title, description=description)
            return f"Log updated successfully:\n{log.model_dump_json(indent=2)}"

        @server.tool()
        def delete_log(
            log_id: str = Field(..., description="The ID of the log to delete"),
        ) -> str:
            """Permanently delete a log and its associated entries."""
            client = _require_logger()
            client.delete_log(log_id)
            return f"Log {log_id} deleted successfully."

        @server.tool()
        def create_log_entry(
            log_id: str = Field(..., description="The ID of the log to attach the entry to"),
            text: str = Field(..., description="The text content of the new log entry"),
        ) -> str:
            """Append a new text entry to a specific log."""
            client = _require_logger()
            entry = client.create_log_entry(log_id, text)
            return f"Log entry created successfully:\n{entry.model_dump_json(indent=2)}"

        @server.tool()
        def update_log_entry(
            entry_id: str = Field(..., description="The ID of the log entry to update"),
            text: str = Field(..., description="The new text content of the log entry"),
        ) -> str:
            """Modify the text content of a specific log entry."""
            client = _require_logger()
            entry = client.update_log_entry(entry_id, text)
            return f"Log entry updated successfully:\n{entry.model_dump_json(indent=2)}"

        @server.tool()
        def delete_log_entry(
            entry_id: str = Field(..., description="The ID of the log entry to delete"),
        ) -> str:
            """Permanently delete a log entry."""
            client = _require_logger()
            client.delete_log_entry(entry_id)
            return f"Log entry {entry_id} deleted successfully."

        @server.tool()
        def create_campaign_entry(
            campaign_id: str = Field(..., description="The ID of the campaign to attach the page to"),
            text: str = Field(..., description="The text content of the new campaign page"),
        ) -> str:
            """Create a new top-level page (Campaign Entry) attached to a specific campaign."""
            client = _require_logger()
            entry = client.create_campaign_entry(campaign_id, text)
            return f"Campaign entry (page) created successfully:\n{entry.model_dump_json(indent=2)}"

        @server.tool()
        def update_campaign_entry(
            entry_id: str = Field(..., description="The ID of the campaign entry (page) to update"),
            text: str = Field(..., description="The new text content of the campaign page"),
        ) -> str:
            """Modify the text content of a specific campaign page."""
            client = _require_logger()
            entry = client.update_campaign_entry(entry_id, text)
            return f"Campaign entry (page) updated successfully:\n{entry.model_dump_json(indent=2)}"

        @server.tool()
        def delete_campaign_entry(
            entry_id: str = Field(..., description="The ID of the campaign entry (page) to delete"),
        ) -> str:
            """Permanently delete a campaign page."""
            client = _require_logger()
            client.delete_campaign_entry(entry_id)
            return f"Campaign entry (page) {entry_id} deleted successfully."

    return server


def run_mcp_server(read_only: bool = False) -> None:
    """Run the Campaign Logger MCP server."""
    server = create_mcp_server(read_only=read_only)
    server.run()
