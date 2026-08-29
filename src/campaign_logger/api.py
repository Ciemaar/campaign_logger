"""API clients for interacting with Campaign Logger."""

from typing import Any

import requests

from .models import Campaign
from .models import CampaignEntry
from .models import GeneratorModel
from .models import Log
from .models import LogEntry


class GeneratorClient:
    """Client for the Campaign Logger Generator API."""

    def __init__(
        self,
        base_url: str = "https://generator.campaign-logger.com",
        token: str | None = None,
    ):
        """Initialize the Generator API client."""
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        if token:  # pragma: no cover
            self.session.headers.update({"Authorization": f"Bearer {token}"})

        self.session.headers.update({"Content-Type": "application/json"})  # pragma: no cover

    def _parse_generator(self, generator_data: dict[str, Any]) -> GeneratorModel:
        """Parse raw dictionary into a GeneratorModel and inject the client."""
        model = GeneratorModel(**generator_data)
        model._client = self
        return model

    def list_generators(self) -> list[GeneratorModel]:
        """Retrieve a list of all generators accessible to the currently authenticated user."""
        url = f"{self.base_url}/api2/generators"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        generators = data.get("generators", data) if isinstance(data, dict) else data
        return [self._parse_generator(g) for g in generators]

    def get_generator(self, generator_id: str) -> GeneratorModel:
        """Fetch a specific generator by its unique identifier."""
        url = f"{self.base_url}/api2/generators/{generator_id}"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        # Sometimes individual requests are nested under a list in 'generators' key too
        if isinstance(data, dict) and "generators" in data:
            data = data["generators"][0] if data["generators"] else data
        return self._parse_generator(data)

    def get_generator_by_name(self, name: str) -> GeneratorModel | None:
        """Fetch a specific generator by its exact name."""
        generators = self.list_generators()
        for gen in generators:
            if gen.name == name:
                return gen
        return None

    def create_generator(self, model: GeneratorModel) -> GeneratorModel:
        """Create and store a new generator based on the provided model payload."""
        url = f"{self.base_url}/api2/generators"
        response = self.session.post(url, json=model.model_dump(exclude_unset=True, exclude={"_client"}))
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "generators" in data:
            data = data["generators"][0] if data["generators"] else data
        return self._parse_generator(data)

    def update_generator(self, generator_id: str, model: GeneratorModel) -> GeneratorModel:
        """Update an existing generator.

        This performs a full overwrite of the generator matching the specified ID using the provided payload.
        """
        url = f"{self.base_url}/api2/generators/{generator_id}"
        response = self.session.put(url, json=model.model_dump(exclude_unset=True, exclude={"_client"}))
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "generators" in data:
            data = data["generators"][0] if data["generators"] else data
        return self._parse_generator(data)

    def delete_generator(self, generator_id: str) -> None:
        """Permanently delete the generator associated with the given identifier."""
        url = f"{self.base_url}/api2/generators/{generator_id}"
        response = self.session.delete(url)
        response.raise_for_status()

    def validate_generator(self, model: GeneratorModel) -> None:
        """Run validation rules against the provided generator payload without saving it."""
        url = f"{self.base_url}/api2/generators/validate"
        response = self.session.post(url, json=model.model_dump(exclude_unset=True, exclude={"_client"}))
        response.raise_for_status()

    def generate(self, model: GeneratorModel) -> dict[str, Any]:
        """Execute a generation process using the rules and tables defined in the provided payload."""
        url = f"{self.base_url}/api2/generators/generate"
        response = self.session.post(url, json=model.model_dump(exclude_unset=True, exclude={"_client"}))
        response.raise_for_status()
        return response.json()

    def execute_operation(self, generator_id: str, operation: str) -> dict[str, Any]:
        """Perform a remote operation (such as 'validate' or 'generate') on an already saved generator."""
        if operation not in ["validate", "generate"]:
            raise ValueError("Operation must be 'validate' or 'generate'")
        url = f"{self.base_url}/api2/generators/{generator_id}/{operation}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json() if response.content else {}

    def get_execute_tokens(self, generator_id: str) -> list[str]:
        """Retrieve all active execution tokens associated with a specific generator."""
        url = f"{self.base_url}/api2/generators/{generator_id}/execute-tokens"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def create_execute_token(self, generator_id: str) -> str:
        """Mint a new execution token for a specific generator to allow stateless execution."""
        url = f"{self.base_url}/api2/generators/{generator_id}/execute-tokens"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()

    def delete_execute_token(self, generator_id: str, token: str) -> None:
        """Revoke and delete a specific execution token belonging to a generator."""
        url = f"{self.base_url}/api2/generators/{generator_id}/execute-tokens/{token}"
        response = self.session.delete(url)
        response.raise_for_status()


class LoggerClient:
    """Client for the main Campaign Logger JSON:API."""

    def __init__(
        self,
        base_url: str = "https://logger.campaign-logger.com",
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        """Initialize the Logger API client."""
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        if client_id and client_secret:  # pragma: no cover
            self.session.headers.update({"api-client": client_id, "api-secret": client_secret})

        self.session.headers.update(
            {
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
            }
        )  # pragma: no cover

    def _get(self, resource_type: str, item_id: str | None = None) -> dict[str, Any]:
        """Get a resource from the API."""
        url = f"{self.base_url}/{resource_type}"
        if item_id:
            url = f"{url}/{item_id}"
        response = self.session.get(url)
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.JSONDecodeError as e:
            raise requests.exceptions.HTTPError(f"Failed to parse JSON response: {response.text}", response=response) from e

    def _delete(self, resource_type: str, item_id: str) -> None:
        """Delete a resource from the API."""
        url = f"{self.base_url}/{resource_type}/{item_id}"
        response = self.session.delete(url)
        response.raise_for_status()

    def _parse_campaign(self, resource: dict[str, Any]) -> Campaign:
        attrs = resource.get("attributes", {})
        camp = Campaign(
            id=str(resource.get("id", "")),
            type=resource.get("type", ""),
            title=str(attrs.get("title", "")),
            description=str(attrs.get("description", "")),
        )
        camp._client = self
        return camp

    def _parse_log(self, resource: dict[str, Any]) -> Log:
        attrs = resource.get("attributes", {})
        rels = resource.get("relationships", {})
        campaign_rel = rels.get("campaign", {}).get("data", {})
        campaign_id = str(attrs.get("campaignId", attrs.get("campaign-id", "")))
        if not campaign_id and campaign_rel:
            campaign_id = str(campaign_rel.get("id", ""))

        log_obj = Log(
            id=str(resource.get("id", "")),
            type=resource.get("type", ""),
            title=str(attrs.get("title", "")),
            description=str(attrs.get("description", "")),
            campaign_id=campaign_id,
        )
        log_obj._client = self
        return log_obj

    def _parse_log_entry(self, resource: dict[str, Any]) -> LogEntry:
        attrs = resource.get("attributes", {})
        rels = resource.get("relationships", {})
        log_rel = rels.get("log", {}).get("data", {})

        raw_text = str(attrs.get("rawText", attrs.get("raw-text", "")))
        title = str(attrs.get("title", ""))

        log_id = str(attrs.get("logId", attrs.get("log-id", "")))
        if not log_id and log_rel:
            log_id = str(log_rel.get("id", ""))

        entry = LogEntry(
            id=str(resource.get("id", "")),
            type=resource.get("type", ""),
            raw_text=raw_text,
            title=title if title else None,
            log_id=log_id,
        )
        entry._client = self
        return entry

    def _parse_campaign_entry(self, resource: dict[str, Any]) -> CampaignEntry:
        attrs = resource.get("attributes", {})
        rels = resource.get("relationships", {})
        campaign_rel = rels.get("campaign", {}).get("data", {})

        raw_text = str(attrs.get("rawText", attrs.get("raw-text", "")))
        raw_public = str(attrs.get("rawPublic", attrs.get("raw-public", "")))
        tag_symbol = str(attrs.get("tagSymbol", attrs.get("tag-symbol", "")))
        tag_value = str(attrs.get("tagValue", attrs.get("tag-value", "")))

        # In Campaign Logger, the full content of a page is sometimes spread out.
        # If raw-text is empty but raw-public is set, combine tag info and raw-public.
        if not raw_text and raw_public:
            title_prefix = f"{tag_symbol}{tag_value}\n" if tag_symbol and tag_value else ""
            raw_text = f"{title_prefix}{raw_public}".strip()

        campaign_id = str(attrs.get("campaignId", attrs.get("campaign-id", "")))
        if not campaign_id and campaign_rel:
            campaign_id = str(campaign_rel.get("id", ""))

        entry = CampaignEntry(
            id=str(resource.get("id", "")),
            type=resource.get("type", ""),
            raw_text=raw_text,
            tag_value=tag_value if tag_value else None,
            campaign_id=campaign_id,
        )
        entry._client = self
        return entry

    # --- Campaigns ---
    def get_campaigns(self) -> list[Campaign]:
        """Retrieve all campaigns available to the authenticated API Client."""
        response = self._get("campaigns")
        data = response.get("data", [])
        if not isinstance(data, list):
            data = [data]
        return [self._parse_campaign(r) for r in data]

    def get_campaign(self, campaign_id: str) -> Campaign:
        """Retrieve a specific campaign by its unique identifier."""
        response = self._get("campaigns", campaign_id)
        data = response.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_campaign(data)

    def create_campaign(self, title: str, description: str = "") -> Campaign:
        """Create a new top-level campaign entity."""
        url = f"{self.base_url}/campaigns"
        payload: dict[str, Any] = {
            "data": {
                "type": "campaigns",
                "attributes": {
                    "title": title,
                    "description": description,
                },
            }
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        json_resp = response.json()
        data = json_resp.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_campaign(data)

    def update_campaign(self, campaign_id: str, title: str | None = None, description: str | None = None) -> Campaign:
        """Update the metadata (title or description) of an existing campaign."""
        url = f"{self.base_url}/campaigns/{campaign_id}"
        attributes: dict[str, Any] = {}
        if title is not None:
            attributes["title"] = title
        if description is not None:
            attributes["description"] = description

        payload: dict[str, Any] = {"data": {"type": "campaigns", "id": campaign_id, "attributes": attributes}}
        response = self.session.patch(url, json=payload)
        response.raise_for_status()
        json_resp = response.json()
        data = json_resp.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_campaign(data)

    def delete_campaign(self, campaign_id: str) -> None:
        """Permanently delete a campaign and its associated contents."""
        self._delete("campaigns", campaign_id)

    # --- Logs ---
    def get_logs(self) -> list[Log]:
        """Retrieve all logs available across the user's campaigns."""
        response = self._get("logs")
        data = response.get("data", [])
        if not isinstance(data, list):
            data = [data]
        return [self._parse_log(r) for r in data]

    def get_log(self, log_id: str) -> Log:
        """Retrieve a specific log by its unique identifier."""
        response = self._get("logs", log_id)
        data = response.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_log(data)

    def create_log(self, campaign_id: str, title: str, description: str = "") -> Log:
        """Create a new child log attached to a specific campaign."""
        url = f"{self.base_url}/logs"
        payload: dict[str, Any] = {
            "data": {
                "type": "logs",
                "attributes": {
                    "title": title,
                    "description": description,
                    "campaignId": campaign_id,
                },
                "relationships": {"campaign": {"data": {"type": "campaigns", "id": campaign_id}}},
            }
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        json_resp = response.json()
        data = json_resp.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_log(data)

    def update_log(self, log_id: str, title: str | None = None, description: str | None = None) -> Log:
        """Update the metadata (title or description) of an existing log."""
        url = f"{self.base_url}/logs/{log_id}"
        attributes: dict[str, Any] = {}
        if title is not None:
            attributes["title"] = title
        if description is not None:
            attributes["description"] = description

        payload: dict[str, Any] = {"data": {"type": "logs", "id": log_id, "attributes": attributes}}
        response = self.session.patch(url, json=payload)
        response.raise_for_status()
        json_resp = response.json()
        data = json_resp.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_log(data)

    def delete_log(self, log_id: str) -> None:
        """Permanently delete a log and its associated entries."""
        self._delete("logs", log_id)

    # --- Log Entries ---
    def get_log_entries(self, log_id: str | None = None) -> list[LogEntry]:
        """Retrieve all individual log entries across the user's logs."""
        response = self._get("log-entries")
        data = response.get("data", [])
        if not isinstance(data, list):
            data = [data]
        entries = [self._parse_log_entry(r) for r in data]
        if log_id:
            entries = [e for e in entries if e.log_id == log_id]
        return entries

    def get_log_entry(self, entry_id: str) -> LogEntry:
        """Retrieve a specific log entry by its unique identifier."""
        response = self._get("log-entries", entry_id)
        data = response.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_log_entry(data)

    def create_log_entry(self, log_id: str, raw_text: str) -> LogEntry:
        """Create a new text entry attached to a specific log."""
        url = f"{self.base_url}/log-entries"
        payload: dict[str, Any] = {
            "data": {
                "type": "log-entries",
                "attributes": {
                    "rawText": raw_text,
                    "logId": log_id,
                },
                "relationships": {"log": {"data": {"type": "logs", "id": log_id}}},
            }
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        json_resp = response.json()
        data = json_resp.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_log_entry(data)

    def update_log_entry(self, entry_id: str, raw_text: str) -> LogEntry:
        """Update the textual content of an existing log entry."""
        url = f"{self.base_url}/log-entries/{entry_id}"
        payload: dict[str, Any] = {
            "data": {
                "type": "log-entries",
                "id": entry_id,
                "attributes": {
                    "rawText": raw_text,
                },
            }
        }
        response = self.session.patch(url, json=payload)
        response.raise_for_status()
        json_resp = response.json()
        data = json_resp.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_log_entry(data)

    def delete_log_entry(self, entry_id: str) -> None:
        """Permanently delete a specific log entry."""
        self._delete("log-entries", entry_id)

    # --- Campaign Entries (Pages) ---
    def get_campaign_entries(self, campaign_id: str | None = None) -> list[CampaignEntry]:
        """Retrieve all campaign entries (pages) across the user's campaigns."""
        response = self._get("campaign-entries")
        data = response.get("data", [])
        if not isinstance(data, list):
            data = [data]
        entries = [self._parse_campaign_entry(r) for r in data]
        if campaign_id:
            entries = [e for e in entries if e.campaign_id == campaign_id]
        return entries

    def get_campaign_entry(self, entry_id: str) -> CampaignEntry:
        """Retrieve a specific campaign entry (page) by its unique identifier."""
        response = self._get("campaign-entries", entry_id)
        data = response.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_campaign_entry(data)

    def create_campaign_entry(self, campaign_id: str, raw_text: str) -> CampaignEntry:
        """Create a new top-level page (Campaign Entry) attached to a specific campaign."""
        url = f"{self.base_url}/campaign-entries"
        payload: dict[str, Any] = {
            "data": {
                "type": "campaign-entries",
                "attributes": {
                    "rawText": raw_text,
                    "campaignId": campaign_id,
                },
                "relationships": {"campaign": {"data": {"type": "campaigns", "id": campaign_id}}},
            }
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        json_resp = response.json()
        data = json_resp.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_campaign_entry(data)

    def update_campaign_entry(self, entry_id: str, raw_text: str) -> CampaignEntry:
        """Update the text content of an existing campaign entry (page)."""
        url = f"{self.base_url}/campaign-entries/{entry_id}"
        payload: dict[str, Any] = {
            "data": {
                "type": "campaign-entries",
                "id": entry_id,
                "attributes": {
                    "rawText": raw_text,
                },
            }
        }
        response = self.session.patch(url, json=payload)
        response.raise_for_status()
        json_resp = response.json()
        data = json_resp.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_campaign_entry(data)

    def delete_campaign_entry(self, entry_id: str) -> None:
        """Permanently delete a specific campaign entry (page)."""
        self._delete("campaign-entries", entry_id)
