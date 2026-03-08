"""API clients for interacting with Campaign Logger."""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import requests

from .models import FullGeneratorModel
from .models import JsonApiResponse


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

        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        if client_id and client_secret:
            self.session.headers.update({"api-client": client_id, "api-secret": client_secret})

        self.session.headers.update({"Content-Type": "application/json"})

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

        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

        self.session.headers.update(
            {
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
            }
        )

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

    # --- Campaigns ---
    def get_campaigns(self) -> JsonApiResponse:
        """Get all campaigns."""
        return self._get("campaigns")

    def get_campaign(self, campaign_id: str) -> JsonApiResponse:
        """Get a campaign by ID."""
        return self._get("campaigns", campaign_id)

    def create_campaign(self, title: str, description: str = "") -> JsonApiResponse:
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
        return JsonApiResponse(**response.json())

    def update_campaign(self, campaign_id: str, title: Optional[str] = None, description: Optional[str] = None) -> JsonApiResponse:
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
        return JsonApiResponse(**response.json())

    def delete_campaign(self, campaign_id: str) -> None:
        """Delete a campaign."""
        self._delete("campaigns", campaign_id)

    # --- Logs ---
    def get_logs(self) -> JsonApiResponse:
        """Get all logs."""
        return self._get("logs")

    def get_log(self, log_id: str) -> JsonApiResponse:
        """Get a log by ID."""
        return self._get("logs", log_id)

    def create_log(self, campaign_id: str, title: str, description: str = "") -> JsonApiResponse:
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
        return JsonApiResponse(**response.json())

    def update_log(self, log_id: str, title: Optional[str] = None, description: Optional[str] = None) -> JsonApiResponse:
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
        return JsonApiResponse(**response.json())

    def delete_log(self, log_id: str) -> None:
        """Delete a log."""
        self._delete("logs", log_id)

    # --- Log Entries ---
    def get_log_entries(self) -> JsonApiResponse:
        """Get all log entries."""
        return self._get("log-entries")

    def get_log_entry(self, entry_id: str) -> JsonApiResponse:
        """Get a log entry by ID."""
        return self._get("log-entries", entry_id)

    def create_log_entry(self, log_id: str, raw_text: str) -> JsonApiResponse:
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
        return JsonApiResponse(**response.json())

    def update_log_entry(self, entry_id: str, raw_text: str) -> JsonApiResponse:
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
        return JsonApiResponse(**response.json())

    def delete_log_entry(self, entry_id: str) -> None:
        """Delete a log entry."""
        self._delete("log-entries", entry_id)

    # --- Campaign Entries (Pages) ---
    def get_campaign_entries(self) -> JsonApiResponse:
        """Get all campaign entries."""
        return self._get("campaign-entries")

    def get_campaign_entry(self, entry_id: str) -> JsonApiResponse:
        """Get a campaign entry by ID."""
        return self._get("campaign-entries", entry_id)

    def create_campaign_entry(self, campaign_id: str, raw_text: str) -> JsonApiResponse:
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
        return JsonApiResponse(**response.json())

    def update_campaign_entry(self, entry_id: str, raw_text: str) -> JsonApiResponse:
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
        return JsonApiResponse(**response.json())

    def delete_campaign_entry(self, entry_id: str) -> None:
        """Delete a campaign entry."""
        self._delete("campaign-entries", entry_id)
