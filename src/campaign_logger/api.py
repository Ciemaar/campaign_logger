"""API clients for interacting with Campaign Logger."""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import requests

from .models import Campaign
from .models import CampaignEntry
from .models import FullGeneratorModel
from .models import JsonApiResource
from .models import JsonApiResponse
from .models import Log
from .models import LogEntry


class GeneratorClient:
    """Client for the Campaign Logger Generator API."""

    def __init__(
        self,
        base_url: str = "https://generator.campaign-logger.com",
        token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """Initialize the Generator API client."""
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        if token:  # pragma: no cover
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        if client_id and client_secret:  # pragma: no cover
            self.session.headers.update({"api-client": client_id, "api-secret": client_secret})

        self.session.headers.update({"Content-Type": "application/json"})  # pragma: no cover

    def list_generators(self) -> List[FullGeneratorModel]:
        """Gets all generators of the current user."""
        url = f"{self.base_url}/api2/generators"
        response = self.session.get(url)
        response.raise_for_status()
        # Assuming the API returns a list of FullGeneratorModel
        return [FullGeneratorModel(**g) for g in response.json()]

    def get_generator(self, generator_id: str) -> FullGeneratorModel:
        """Gets the generator identified by {id}."""
        url = f"{self.base_url}/api2/generators/{generator_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return FullGeneratorModel(**response.json())

    def create_generator(self, model: FullGeneratorModel) -> FullGeneratorModel:
        """Stores the generator provided in the body of the request."""
        url = f"{self.base_url}/api2/generators"
        response = self.session.post(url, json=model.model_dump(exclude_unset=True))
        response.raise_for_status()
        return FullGeneratorModel(**response.json())

    def update_generator(self, generator_id: str, model: FullGeneratorModel) -> FullGeneratorModel:
        """Updates the generator identified by {id}.

        Overwrites it with the request body.
        """
        url = f"{self.base_url}/api2/generators/{generator_id}"
        response = self.session.put(url, json=model.model_dump(exclude_unset=True))
        response.raise_for_status()
        return FullGeneratorModel(**response.json())

    def delete_generator(self, generator_id: str) -> None:
        """Deletes the generator identified by {id}."""
        url = f"{self.base_url}/api2/generators/{generator_id}"
        response = self.session.delete(url)
        response.raise_for_status()

    def validate_generator(self, model: FullGeneratorModel) -> None:
        """Executes validate on the generator provided in the body."""
        url = f"{self.base_url}/api2/generators/validate"
        response = self.session.post(url, json=model.model_dump(exclude_unset=True))
        response.raise_for_status()

    def generate_random(self, model: FullGeneratorModel) -> Dict[str, Any]:
        """Executes generate on the generator provided in the body."""
        url = f"{self.base_url}/api2/generators/generate"
        response = self.session.post(url, json=model.model_dump(exclude_unset=True))
        response.raise_for_status()
        return response.json()

    def execute_operation(self, generator_id: str, operation: str) -> Dict[str, Any]:
        """Executes {operation} on the generator identified by {id}."""
        if operation not in ["validate", "generate"]:
            raise ValueError("Operation must be 'validate' or 'generate'")
        url = f"{self.base_url}/api2/generators/{generator_id}/{operation}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json() if response.content else {}

    def get_execute_tokens(self, generator_id: str) -> List[str]:
        """Gets all execute-tokens for the generator identified by {id}."""
        url = f"{self.base_url}/api2/generators/{generator_id}/execute-tokens"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def create_execute_token(self, generator_id: str) -> str:
        """Creates a new execute-token for the generator identified by {id}."""
        url = f"{self.base_url}/api2/generators/{generator_id}/execute-tokens"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()

    def delete_execute_token(self, generator_id: str, token: str) -> None:
        """Deletes the execute-token {token} for the generator identified by {id}."""
        url = f"{self.base_url}/api2/generators/{generator_id}/execute-tokens/{token}"
        response = self.session.delete(url)
        response.raise_for_status()


class LoggerClient:
    """Client for the main Campaign Logger JSON:API."""

    def __init__(
        self,
        base_url: str = "https://logger.campaign-logger.com",
        token: Optional[str] = None,
    ):
        """Initialize the Logger API client."""
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        if token:  # pragma: no cover
            self.session.headers.update({"Authorization": f"Bearer {token}"})

        self.session.headers.update(
            {
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
            }
        )  # pragma: no cover

    def _get(self, resource_type: str, item_id: Optional[str] = None) -> JsonApiResponse:
        """Get a resource from the API."""
        url = f"{self.base_url}/{resource_type}"
        if item_id:
            url = f"{url}/{item_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return JsonApiResponse(**response.json())

    def _delete(self, resource_type: str, item_id: str) -> None:
        """Delete a resource from the API."""
        url = f"{self.base_url}/{resource_type}/{item_id}"
        response = self.session.delete(url)
        response.raise_for_status()

    def _parse_campaign(self, resource: JsonApiResource) -> Campaign:
        attrs = resource.attributes or {}
        camp = Campaign(
            id=str(resource.id),
            type=resource.type,
            title=str(attrs.get("title", "")),
            description=str(attrs.get("description", "")),
        )
        camp._client = self
        return camp

    def _parse_log(self, resource: JsonApiResource) -> Log:
        attrs = resource.attributes or {}
        log_obj = Log(
            id=str(resource.id),
            type=resource.type,
            title=str(attrs.get("title", "")),
            description=str(attrs.get("description", "")),
            campaign_id=str(attrs.get("campaignId", "")),
        )
        log_obj._client = self
        return log_obj

    def _parse_log_entry(self, resource: JsonApiResource) -> LogEntry:
        attrs = resource.attributes or {}
        entry = LogEntry(
            id=str(resource.id),
            type=resource.type,
            raw_text=str(attrs.get("rawText", "")),
            log_id=str(attrs.get("logId", "")),
        )
        entry._client = self
        return entry

    def _parse_campaign_entry(self, resource: JsonApiResource) -> CampaignEntry:
        attrs = resource.attributes or {}
        entry = CampaignEntry(
            id=str(resource.id),
            type=resource.type,
            raw_text=str(attrs.get("rawText", "")),
            campaign_id=str(attrs.get("campaignId", "")),
        )
        entry._client = self
        return entry

    # --- Campaigns ---
    def get_campaigns(self) -> List[Campaign]:
        """Get all campaigns."""
        response = self._get("campaigns")
        data = response.data if isinstance(response.data, list) else [response.data]
        return [self._parse_campaign(r) for r in data]

    def get_campaign(self, campaign_id: str) -> Campaign:
        """Get a campaign by ID."""
        response = self._get("campaigns", campaign_id)
        if isinstance(response.data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_campaign(response.data)

    def create_campaign(self, title: str, description: str = "") -> Campaign:
        """Create a new campaign."""
        url = f"{self.base_url}/campaigns"
        payload = {
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
        json_resp = JsonApiResponse(**response.json())
        if isinstance(json_resp.data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_campaign(json_resp.data)

    def update_campaign(self, campaign_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Campaign:
        """Update an existing campaign."""
        url = f"{self.base_url}/campaigns/{campaign_id}"
        attributes: Dict[str, Any] = {}
        if title is not None:
            attributes["title"] = title
        if description is not None:
            attributes["description"] = description

        payload = {"data": {"type": "campaigns", "id": campaign_id, "attributes": attributes}}
        response = self.session.patch(url, json=payload)
        response.raise_for_status()
        json_resp = JsonApiResponse(**response.json())
        if isinstance(json_resp.data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_campaign(json_resp.data)

    def delete_campaign(self, campaign_id: str) -> None:
        """Delete a campaign."""
        self._delete("campaigns", campaign_id)

    # --- Logs ---
    def get_logs(self) -> List[Log]:
        """Get all logs."""
        response = self._get("logs")
        data = response.data if isinstance(response.data, list) else [response.data]
        return [self._parse_log(r) for r in data]

    def get_log(self, log_id: str) -> Log:
        """Get a log by ID."""
        response = self._get("logs", log_id)
        if isinstance(response.data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_log(response.data)

    def create_log(self, campaign_id: str, title: str, description: str = "") -> Log:
        """Create a new log."""
        url = f"{self.base_url}/logs"
        payload = {
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
        json_resp = JsonApiResponse(**response.json())
        if isinstance(json_resp.data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_log(json_resp.data)

    def update_log(self, log_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Log:
        """Update an existing log."""
        url = f"{self.base_url}/logs/{log_id}"
        attributes: Dict[str, Any] = {}
        if title is not None:
            attributes["title"] = title
        if description is not None:
            attributes["description"] = description

        payload = {"data": {"type": "logs", "id": log_id, "attributes": attributes}}
        response = self.session.patch(url, json=payload)
        response.raise_for_status()
        json_resp = JsonApiResponse(**response.json())
        if isinstance(json_resp.data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_log(json_resp.data)

    def delete_log(self, log_id: str) -> None:
        """Delete a log."""
        self._delete("logs", log_id)

    # --- Log Entries ---
    def get_log_entries(self) -> List[LogEntry]:
        """Get all log entries."""
        response = self._get("log-entries")
        data = response.data if isinstance(response.data, list) else [response.data]
        return [self._parse_log_entry(r) for r in data]

    def get_log_entry(self, entry_id: str) -> LogEntry:
        """Get a log entry by ID."""
        response = self._get("log-entries", entry_id)
        if isinstance(response.data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_log_entry(response.data)

    def create_log_entry(self, log_id: str, raw_text: str) -> LogEntry:
        """Create a new log entry."""
        url = f"{self.base_url}/log-entries"
        payload = {
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
        json_resp = JsonApiResponse(**response.json())
        if isinstance(json_resp.data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_log_entry(json_resp.data)

    def update_log_entry(self, entry_id: str, raw_text: str) -> LogEntry:
        """Update an existing log entry."""
        url = f"{self.base_url}/log-entries/{entry_id}"
        payload = {
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
        json_resp = JsonApiResponse(**response.json())
        if isinstance(json_resp.data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_log_entry(json_resp.data)

    def delete_log_entry(self, entry_id: str) -> None:
        """Delete a log entry."""
        self._delete("log-entries", entry_id)

    # --- Campaign Entries (Pages) ---
    def get_campaign_entries(self) -> List[CampaignEntry]:
        """Get all campaign entries."""
        response = self._get("campaign-entries")
        data = response.data if isinstance(response.data, list) else [response.data]
        return [self._parse_campaign_entry(r) for r in data]

    def get_campaign_entry(self, entry_id: str) -> CampaignEntry:
        """Get a campaign entry by ID."""
        response = self._get("campaign-entries", entry_id)
        if isinstance(response.data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_campaign_entry(response.data)

    def create_campaign_entry(self, campaign_id: str, raw_text: str) -> CampaignEntry:
        """Creates a page (Campaign Entry) in a campaign."""
        url = f"{self.base_url}/campaign-entries"
        payload = {
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
        json_resp = JsonApiResponse(**response.json())
        if isinstance(json_resp.data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_campaign_entry(json_resp.data)

    def update_campaign_entry(self, entry_id: str, raw_text: str) -> CampaignEntry:
        """Update an existing campaign entry."""
        url = f"{self.base_url}/campaign-entries/{entry_id}"
        payload = {
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
        json_resp = JsonApiResponse(**response.json())
        if isinstance(json_resp.data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_campaign_entry(json_resp.data)

    def delete_campaign_entry(self, entry_id: str) -> None:
        """Delete a campaign entry."""
        self._delete("campaign-entries", entry_id)
