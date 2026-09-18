"""Pydantic models for Campaign Logger APIs."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import PrivateAttr
from pydantic import field_validator


def _to_kebab(field_name: str) -> str:
    """Map a snake_case field to the kebab-case key the API sends on the wire.

    The wire format is kebab-case (``created-on``, ``raw-text``); the swagger
    schema names are camelCase but that is not what crosses the wire. We support
    only what the API actually sends. See docs/live_testing_evidence.md.
    """
    return field_name.replace("_", "-")


class VariableModel(BaseModel):
    """Model representing a variable in a Generator."""

    v: Any | None = Field(None, description="The value of the variable.")


class EntryModel(BaseModel):
    """Model representing a single text entry or result inside a Table."""

    m: int | None = Field(None, ge=0, le=1024, description="Multiplier or relative weight of this entry.")
    v: str | None = Field(None, description="The text value or pattern for this entry.")
    export: dict[str, VariableModel] | None = Field(None, description="Variables to export when this entry is selected.")
    set: dict[str, VariableModel] | None = Field(None, description="Variables to set when this entry is selected.")


class TableModel(BaseModel):
    """Model representing a table of random outcomes within a Generator."""

    name: str | None = Field(None, description="The name of the table.")
    explanation: str | None = Field(None, description="Description or explanation of the table's purpose.")
    export: dict[str, VariableModel] | None = Field(None, description="Variables exported globally from this table.")
    set: dict[str, VariableModel] | None = Field(None, description="Variables set locally in this table.")
    entries: list[EntryModel] | None = Field(None, description="The list of possible entries in this table.")


class GeneratorModel(BaseModel):
    """Model representing a complete Campaign Logger Generator definition."""

    id: str | None = Field(None, description="The unique identifier for the generator.")
    name: str | None = Field(None, description="The display name of the generator.")
    explanation: str | None = Field(None, description="A description or explanation of the generator.")
    path: str | None = Field(None, description="The organizational path where this generator is stored.")
    categories: list[str] | None = Field(None, description="List of category tags applied to this generator.")
    formatting: int | None = Field(None, description="Formatting flag for the output (0 or 1).")
    resultPattern: str | None = Field(None, description="The pattern defining how the final generated result is structured.")
    wrapResultInCurlyBraces: bool | None = Field(False, description=("Whether the final result string should be wrapped in curly braces."))
    globals: dict[str, VariableModel] | None = Field(None, description="Global variables defined for the generator.")
    variables: dict[str, VariableModel] | None = Field(None, description="Local variables defined for the generator.")
    tables: list[TableModel] | None = Field(None, description="The collection of tables used by the generator.")

    _client: Any = PrivateAttr(default=None)

    def validate_generator(self) -> None:
        """Run validation rules against this generator payload."""
        client = getattr(self, "_client")
        client.validate_generator(self)

    def generate(self) -> dict[str, Any]:
        """Execute a generation process using this generator."""
        client = getattr(self, "_client")
        return client.generate(self)

    def save(self) -> "GeneratorModel":
        """Update this existing generator on the remote server."""
        client = getattr(self, "_client")
        if not self.id:
            raise ValueError("Generator does not have an ID to save.")
        return client.update_generator(self.id, self)

    def delete(self) -> None:
        """Delete this generator from the remote server."""
        client = getattr(self, "_client")
        if not self.id:
            raise ValueError("Generator does not have an ID to delete.")
        client.delete_generator(self.id)


# High-Level Object-Oriented Models


class Player(BaseModel):
    """A player invited to or joined into a campaign."""

    model_config = ConfigDict(alias_generator=_to_kebab, populate_by_name=True, extra="ignore")

    email_address: str | None = None
    email_address_case_insensitive: str | None = None
    joined_campaigns: list[str] | None = None


class BaseEntity(BaseModel):
    """Base model for high-level object-oriented wrappers.

    Attributes come off the wire in kebab-case; the ``alias_generator`` maps each
    snake_case field to its kebab-case key, and ``populate_by_name`` still allows
    constructing an entity with the field names directly (as the tests do).
    ``extra="ignore"`` tolerates attributes the model does not yet cover.

    The audit-trail, soft-delete and revision fields below are present on every
    resource in the API, so they live here rather than being repeated.
    """

    model_config = ConfigDict(alias_generator=_to_kebab, populate_by_name=True, extra="ignore")

    id: str
    type: str

    created_on: datetime | None = None
    updated_on: datetime | None = None
    deleted_on: datetime | None = None
    is_deleted: bool = False
    revision: str | None = None
    previous_revision: str | None = None
    string_id: str | None = None
    user_id: str | None = None

    _client: Any = PrivateAttr(default=None)

    @field_validator("created_on", "updated_on", "deleted_on", mode="before")
    @classmethod
    def _empty_string_is_none(cls, value: Any) -> Any:
        """Coerce the API's empty-string timestamp (e.g. ``deleted-on: ""``) to None."""
        if value == "":
            return None
        return value

    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a JSON-safe dictionary for CLI output.

        ``mode="json"`` matters: the timestamp fields are real ``datetime``
        objects, and ``cli.py`` passes this straight to ``json.dumps``, which
        cannot serialise them. This renders them as ISO strings instead.
        """
        return self.model_dump(mode="json")


class LogEntry(BaseEntity):
    """Model representing a Log Entry."""

    raw_text: str | None = None
    title: str | None = None
    log_id: str | None = None
    is_shared: bool = False
    ordering: str | None = None
    raw_prefix: str | None = None
    raw_suffix: str | None = None

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

    raw_text: str | None = None
    tag_value: str | None = None
    campaign_id: str | None = None
    raw_public: str | None = None
    raw_summary: str | None = None
    tag_symbol: str | None = None
    tag_value_case_insensitive: str | None = None
    labels: list[str] | None = None

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

    title: str | None = None
    description: str | None = None
    campaign_id: str | None = None
    image_url: str | None = None
    is_pinned: bool = False

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

    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    invited_players: list[str] | None = None
    joined_players: list[Player] | None = None

    def get_logs(self) -> list[Log]:
        """Get all logs for this campaign."""
        client = getattr(self, "_client")
        logs = client.get_logs()
        return [log for log in logs if log.campaign_id == self.id]

    def create_log(self, title: str, description: str = "") -> Log:
        """Create a new log for this campaign."""
        client = getattr(self, "_client")
        return client.create_log(self.id, title, description)

    def get_player_logs(self) -> list["PlayerLog"]:
        """Get all player logs for this campaign."""
        client = getattr(self, "_client")
        logs = client.get_player_logs()
        return [log for log in logs if log.campaign_id == self.id]

    def create_player_log(self, title: str, description: str = "") -> "PlayerLog":
        """Create a new player log for this campaign."""
        client = getattr(self, "_client")
        return client.create_player_log(self.id, title, description)

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


class PlayerLogEntry(BaseEntity):
    """Model representing a Player Log Entry."""

    raw_text: str | None = None
    title: str | None = None
    log_id: str | None = None
    is_shared: bool = False
    ordering: str | None = None
    raw_prefix: str | None = None
    raw_suffix: str | None = None

    def save(self) -> "PlayerLogEntry":
        """Save changes to this player log entry."""
        client = getattr(self, "_client")
        return client.update_player_log_entry(self.id, self.raw_text)

    def delete(self) -> None:
        """Delete this player log entry."""
        client = getattr(self, "_client")
        client.delete_player_log_entry(self.id)


class PlayerLog(BaseEntity):
    """Model representing a Player Log."""

    title: str | None = None
    description: str | None = None
    campaign_id: str | None = None
    image_url: str | None = None
    is_pinned: bool = False

    def get_entries(self) -> list[PlayerLogEntry]:
        """Get all player log entries for this log."""
        client = getattr(self, "_client")
        entries = client.get_player_log_entries()
        return [entry for entry in entries if entry.log_id == self.id]

    def create_entry(self, raw_text: str) -> PlayerLogEntry:
        """Create a new player log entry for this log."""
        client = getattr(self, "_client")
        return client.create_player_log_entry(self.id, raw_text)

    def save(self) -> "PlayerLog":
        """Save changes to this player log."""
        client = getattr(self, "_client")
        return client.update_player_log(self.id, self.title, self.description)

    def delete(self) -> None:
        """Delete this player log."""
        client = getattr(self, "_client")
        client.delete_player_log(self.id)
