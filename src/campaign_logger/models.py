"""Pydantic models for Campaign Logger APIs."""

from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import PrivateAttr


class VariableModel(BaseModel):
    """Model representing a variable."""

    v: Any | None = Field(None, description="Gets or sets the v.")


class EntryModel(BaseModel):
    """Model representing an entry."""

    m: int | None = Field(None, ge=0, le=1024, description="Gets or sets the m.")
    v: str | None = Field(None, description="Gets or sets the v.")
    export: dict[str, VariableModel] | None = Field(None, description="Gets or sets the export.")
    set: dict[str, VariableModel] | None = Field(None, description="Gets or sets the set.")


class TableModel(BaseModel):
    """Model representing a table."""

    name: str | None = Field(None, description="Gets or sets the name.")
    explanation: str | None = Field(None, description="Gets or sets the explanation.")
    export: dict[str, VariableModel] | None = Field(None, description="Gets or sets the export.")
    set: dict[str, VariableModel] | None = Field(None, description="Gets or sets the set.")
    entries: list[EntryModel] | None = Field(None, description="Gets or sets the entries.")


class FullGeneratorModel(BaseModel):
    """Full generator model."""

    id: str | None = Field(None, description="Gets or sets the identifier.")
    name: str | None = Field(None, description="Gets or sets the name.")
    explanation: str | None = Field(None, description="Gets or sets the explanation.")
    path: str | None = Field(None, description="Gets or sets the path.")
    categories: list[str] | None = Field(None, description="Gets or sets the categories.")
    formatting: int | None = Field(None, description="Gets or sets the formatting. 0 or 1.")
    resultPattern: str | None = Field(None, description="Gets or sets the result pattern.")
    wrapResultInCurlyBraces: bool | None = Field(
        False, description=("Gets or sets a value indicating whether to wrap the result in curly braces.")
    )
    globals: dict[str, VariableModel] | None = Field(None, description="Gets or sets the globals.")
    variables: dict[str, VariableModel] | None = Field(None, description="Gets or sets the variables.")
    tables: list[TableModel] | None = Field(None, description="Gets or sets the tables.")


class GeneratorModelContainer(BaseModel):
    """Container for generator models."""


# High-Level Object-Oriented Models


class BaseEntity(BaseModel):
    """Base model for high-level object-oriented wrappers."""

    id: str
    type: str
    _client: Any = PrivateAttr(default=None)

    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary for CLI output."""
        return self.model_dump()


class LogEntry(BaseEntity):
    """Model representing a Log Entry."""

    raw_text: str
    log_id: str

    def save(self) -> "LogEntry":
        """Save changes to this log entry."""
        client = getattr(self, "_client")
        return client.update_log_entry(self.id, self.raw_text)

    def delete(self) -> None:
        """Delete this log entry."""
        client = getattr(self, "_client")
        client.delete_log_entry(self.id)


class CampaignEntry(BaseEntity):
    """Model representing a Campaign Entry (Page)."""

    raw_text: str
    campaign_id: str

    def save(self) -> "CampaignEntry":
        """Save changes to this campaign entry."""
        client = getattr(self, "_client")
        return client.update_campaign_entry(self.id, self.raw_text)

    def delete(self) -> None:
        """Delete this campaign entry."""
        client = getattr(self, "_client")
        client.delete_campaign_entry(self.id)


class Log(BaseEntity):
    """Model representing a Log."""

    title: str
    description: str
    campaign_id: str

    def get_entries(self) -> list[LogEntry]:
        """Get all log entries for this log."""
        client = getattr(self, "_client")
        entries = client.get_log_entries()
        return [entry for entry in entries if entry.log_id == self.id]

    def create_entry(self, raw_text: str) -> LogEntry:
        """Create a new log entry for this log."""
        client = getattr(self, "_client")
        return client.create_log_entry(self.id, raw_text)

    def save(self) -> "Log":
        """Save changes to this log."""
        client = getattr(self, "_client")
        return client.update_log(self.id, self.title, self.description)

    def delete(self) -> None:
        """Delete this log."""
        client = getattr(self, "_client")
        client.delete_log(self.id)


class Campaign(BaseEntity):
    """Model representing a Campaign."""

    title: str
    description: str

    def get_logs(self) -> list[Log]:
        """Get all logs for this campaign."""
        client = getattr(self, "_client")
        logs = client.get_logs()
        return [log for log in logs if log.campaign_id == self.id]

    def create_log(self, title: str, description: str = "") -> Log:
        """Create a new log for this campaign."""
        client = getattr(self, "_client")
        return client.create_log(self.id, title, description)

    def get_entries(self) -> list[CampaignEntry]:
        """Get all campaign entries (pages) for this campaign."""
        client = getattr(self, "_client")
        entries = client.get_campaign_entries()
        return [entry for entry in entries if entry.campaign_id == self.id]

    def create_entry(self, raw_text: str) -> CampaignEntry:
        """Create a new campaign entry for this campaign."""
        client = getattr(self, "_client")
        return client.create_campaign_entry(self.id, raw_text)

    def save(self) -> "Campaign":
        """Save changes to this campaign."""
        client = getattr(self, "_client")
        return client.update_campaign(self.id, self.title, self.description)

    def delete(self) -> None:
        """Delete this campaign."""
        client = getattr(self, "_client")
        client.delete_campaign(self.id)
