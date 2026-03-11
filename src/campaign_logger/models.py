"""Pydantic models for Campaign Logger APIs."""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import PrivateAttr


class VariableModel(BaseModel):
    """Model representing a variable."""

    v: Optional[Any] = Field(None, description="Gets or sets the v.")


class EntryModel(BaseModel):
    """Model representing an entry."""

    m: Optional[int] = Field(None, ge=0, le=1024, description="Gets or sets the m.")
    v: Optional[str] = Field(None, description="Gets or sets the v.")
    export: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the export.")
    set: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the set.")


class TableModel(BaseModel):
    """Model representing a table."""

    name: Optional[str] = Field(None, description="Gets or sets the name.")
    explanation: Optional[str] = Field(None, description="Gets or sets the explanation.")
    export: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the export.")
    set: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the set.")
    entries: Optional[List[EntryModel]] = Field(None, description="Gets or sets the entries.")


class FullGeneratorModel(BaseModel):
    """Full generator model."""

    id: Optional[str] = Field(None, description="Gets or sets the identifier.")
    name: Optional[str] = Field(None, description="Gets or sets the name.")
    explanation: Optional[str] = Field(None, description="Gets or sets the explanation.")
    path: Optional[str] = Field(None, description="Gets or sets the path.")
    categories: Optional[List[str]] = Field(None, description="Gets or sets the categories.")
    formatting: Optional[int] = Field(None, description="Gets or sets the formatting. 0 or 1.")
    resultPattern: Optional[str] = Field(None, description="Gets or sets the result pattern.")
    wrapResultInCurlyBraces: Optional[bool] = Field(
        False, description=("Gets or sets a value indicating whether to wrap the result in curly braces.")
    )
    globals: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the globals.")
    variables: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the variables.")
    tables: Optional[List[TableModel]] = Field(None, description="Gets or sets the tables.")


class GeneratorModelContainer(BaseModel):
    """Container for generator models."""


# JSON:API Models


class JsonApiResourceIdentifier(BaseModel):
    """Identifier for a JSON:API resource."""

    type: str
    id: str


class JsonApiRelationshipData(BaseModel):
    """Data for a JSON:API relationship."""

    data: Union[JsonApiResourceIdentifier, List[JsonApiResourceIdentifier]]


class JsonApiResource(BaseModel):
    """A JSON:API resource object."""

    type: str
    id: Optional[str] = None
    attributes: Optional[Dict[str, Union[str, int, float, bool, None]]] = None
    relationships: Optional[Dict[str, JsonApiRelationshipData]] = None
    links: Optional[Dict[str, str]] = None


class JsonApiResponse(BaseModel):
    """A JSON:API response document."""

    data: Union[JsonApiResource, List[JsonApiResource]]
    included: Optional[List[JsonApiResource]] = None
    meta: Optional[Dict[str, Union[str, int, float, bool, None]]] = None
    links: Optional[Dict[str, str]] = None


# High-Level Object-Oriented Models


class BaseEntity(BaseModel):
    """Base model for high-level object-oriented wrappers."""

    id: str
    type: str
    _client: Any = PrivateAttr(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entity to a dictionary for CLI output."""
        return self.model_dump()


class LogEntry(BaseEntity):
    """Model representing a Log Entry."""

    raw_text: str
    log_id: str

    def update(self, raw_text: str) -> "LogEntry":
        """Update this log entry."""
        client = getattr(self, "_client")
        return client.update_log_entry(self.id, raw_text)

    def delete(self) -> None:
        """Delete this log entry."""
        client = getattr(self, "_client")
        client.delete_log_entry(self.id)


class CampaignEntry(BaseEntity):
    """Model representing a Campaign Entry (Page)."""

    raw_text: str
    campaign_id: str

    def update(self, raw_text: str) -> "CampaignEntry":
        """Update this campaign entry."""
        client = getattr(self, "_client")
        return client.update_campaign_entry(self.id, raw_text)

    def delete(self) -> None:
        """Delete this campaign entry."""
        client = getattr(self, "_client")
        client.delete_campaign_entry(self.id)


class Log(BaseEntity):
    """Model representing a Log."""

    title: str
    description: str
    campaign_id: str

    def get_entries(self) -> List[LogEntry]:
        """Get all log entries for this log."""
        client = getattr(self, "_client")
        entries = client.get_log_entries()
        return [entry for entry in entries if entry.log_id == self.id]

    def create_entry(self, raw_text: str) -> LogEntry:
        """Create a new log entry for this log."""
        client = getattr(self, "_client")
        return client.create_log_entry(self.id, raw_text)

    def update(self, title: Optional[str] = None, description: Optional[str] = None) -> "Log":
        """Update this log."""
        client = getattr(self, "_client")
        return client.update_log(self.id, title, description)

    def delete(self) -> None:
        """Delete this log."""
        client = getattr(self, "_client")
        client.delete_log(self.id)


class Campaign(BaseEntity):
    """Model representing a Campaign."""

    title: str
    description: str

    def get_logs(self) -> List[Log]:
        """Get all logs for this campaign."""
        client = getattr(self, "_client")
        logs = client.get_logs()
        return [log for log in logs if log.campaign_id == self.id]

    def create_log(self, title: str, description: str = "") -> Log:
        """Create a new log for this campaign."""
        client = getattr(self, "_client")
        return client.create_log(self.id, title, description)

    def get_entries(self) -> List[CampaignEntry]:
        """Get all campaign entries (pages) for this campaign."""
        client = getattr(self, "_client")
        entries = client.get_campaign_entries()
        return [entry for entry in entries if entry.campaign_id == self.id]

    def create_entry(self, raw_text: str) -> CampaignEntry:
        """Create a new campaign entry for this campaign."""
        client = getattr(self, "_client")
        return client.create_campaign_entry(self.id, raw_text)

    def update(self, title: Optional[str] = None, description: Optional[str] = None) -> "Campaign":
        """Update this campaign."""
        client = getattr(self, "_client")
        return client.update_campaign(self.id, title, description)

    def delete(self) -> None:
        """Delete this campaign."""
        client = getattr(self, "_client")
        client.delete_campaign(self.id)
