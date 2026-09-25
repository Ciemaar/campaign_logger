"""API clients for interacting with Campaign Logger."""

import warnings
from typing import Any

import requests

from .models import Campaign
from .models import CampaignEntry
from .models import GeneratorModel
from .models import Log
from .models import LogEntry
from .models import PlayerLog
from .models import PlayerLogEntry

#: How much of an unparseable response body goes into the raised error message.
#: The message reaches pytest output and CI logs, so on a live run this is real
#: campaign content -- bounded here rather than printed whole (issue #62, 0.3).
BODY_PREVIEW_CHARS = 100

#: How many records one page asks for via ``page[size]`` when walking a collection.
#:
#: The size is a round-trip/response-size trade-off, bounded by what the server
#: is known to accept. Live staging served ``page[size]=1000`` against a
#: 551-record collection without clamping and without any documented maximum
#: (#77), so 500 sits well inside the range observed to work while keeping one
#: response small enough to hold comfortably in memory. It also means a normal
#: account -- a few hundred records in a collection -- is still fetched in a
#: single request, and a genuinely large one costs a handful, not dozens.
#:
#: A server that silently clamps the size to something smaller is handled
#: anyway: paging advances by ``page[number]`` and counts the records that
#: actually arrive, never the number it asked for.
PAGE_SIZE = 500

#: Hard ceiling on the requests one collection may cost, so a server that never
#: reports the collection complete cannot spin forever. At :data:`PAGE_SIZE`
#: this allows 25,000 records, far past any real campaign, so reaching it means
#: something is wrong rather than that the data is big.
MAX_PAGE_REQUESTS = 50


class PaginationError(RuntimeError):
    """Raised when a paged collection is still incomplete after the request cap."""


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

        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

        self.session.headers.update({"Content-Type": "application/json"})

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


class LoggerSession(requests.Session):
    """A :class:`requests.Session` that drops the logger API credentials on a cross-host redirect.

    ``requests`` only protects the standard ``Authorization`` header: ``rebuild_auth``
    deletes it when a redirect crosses to a different host and leaves every other header
    in place. The logger API authenticates with the custom headers ``api-client`` and
    ``api-secret``, which therefore travel to whatever host answers a redirect unless they
    are stripped explicitly. See issue #39.

    :class:`LoggerClient` uses this automatically. It is public so that callers building
    their own session -- to add retries, proxies or a custom adapter -- can inherit the
    same protection rather than reimplementing it::

        session = LoggerSession()
        session.mount("https://", HTTPAdapter(max_retries=3))
    """

    AUTH_HEADERS = ("api-client", "api-secret")

    def rebuild_auth(self, prepared_request: requests.PreparedRequest, response: requests.Response) -> None:
        """Strip the custom auth headers whenever requests would strip ``Authorization``."""
        super().rebuild_auth(prepared_request, response)

        old_url = response.request.url
        new_url = prepared_request.url

        # Both are Optional on the requests types. If either is missing we cannot tell
        # whether the host changed, so strip the credentials rather than risk sending them.
        if old_url is None or new_url is None or self.should_strip_auth(old_url, new_url):
            for header in self.AUTH_HEADERS:
                prepared_request.headers.pop(header, None)


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
        self.session = LoggerSession()

        if client_id and client_secret:
            self.session.headers.update({"api-client": client_id, "api-secret": client_secret})

        self.session.headers.update(
            {
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
            }
        )

    def _get(self, resource_type: str, item_id: str | None = None) -> dict[str, Any]:
        """Get a resource from the API, following pagination for a collection.

        A single-resource GET costs one request and its document is returned
        untouched. A collection is walked with ``page[size]`` / ``page[number]``
        until it holds as many records as ``meta.total-records`` promises, and
        returned in the same ``{"data": [...]}`` shape a single page has, with
        every page's resources concatenated in request order. Before this,
        ``_get`` issued one request and returned whatever came back, so a
        collection larger than a page was silently truncated (#77).

        A document with no usable ``meta.total-records`` is returned exactly as
        it arrived: the related-resource routes send no ``meta`` at all, and with
        no total there is nothing to say whether another page exists, so paging
        blindly would either guess or loop. Such a response is therefore still
        as truncated as the server chose to make it -- see #76.

        Args:
            resource_type: The path under the base URL, e.g. ``"log-entries"``.
            item_id: A resource id, for a single-resource GET.

        Returns:
            dict: The JSON:API document, with the whole collection under ``data``.

        Raises:
            PaginationError: If the collection is still incomplete after
                :data:`MAX_PAGE_REQUESTS` requests.
        """
        url = f"{self.base_url}/{resource_type}"
        if item_id:
            return self._get_json(f"{url}/{item_id}")
        return self._get_collection(resource_type, url)

    def _get_collection(self, resource_type: str, url: str) -> dict[str, Any]:
        """Walk a collection's pages and return one document holding all of them."""
        first = self._get_json(url, self._page_params(1))
        data = first.get("data")
        total = self._total_records(first)
        # Not a list: a single resource under a collection URL, nothing to page.
        # No total: nothing to page against. Already complete: no second request,
        # which is the common case and must not cost a wasted round trip.
        if not isinstance(data, list) or total is None or len(data) >= total:
            return first

        items = list(data)
        seen = {key for key in map(self._resource_key, data) if key is not None}
        # Pages 2..MAX_PAGE_REQUESTS, so one collection costs at most that many
        # requests including the first. Falling off the end means the server
        # never reported the collection complete.
        for page_number in range(2, MAX_PAGE_REQUESTS + 1):
            page = self._get_json(url, self._page_params(page_number))
            page_data = page.get("data")
            added = 0
            for resource in page_data if isinstance(page_data, list) else []:
                key = self._resource_key(resource)
                if key is not None:
                    if key in seen:
                        continue
                    seen.add(key)
                items.append(resource)
                added += 1
            if added == 0:
                # Either the collection ran out early -- records deleted between
                # pages leave total-records above what can be read -- or the
                # server keeps handing back the same page. Stop with what we
                # have; spinning would never produce the missing records.
                warnings.warn(
                    f"Pagination of {resource_type} stopped at {len(items)} of {total} records: "
                    f"page {page_number} returned nothing new. The result is incomplete.",
                    # _get_collection <- _get <- the public get_* method <- the caller.
                    stacklevel=4,
                )
                break
            if len(items) >= total:
                break
        else:
            raise PaginationError(
                f"Pagination of {resource_type} hit the {MAX_PAGE_REQUESTS}-request cap with "
                f"{len(items)} of {total} records. Refusing to keep requesting pages; "
                f"raise MAX_PAGE_REQUESTS or PAGE_SIZE if the collection really is this large."
            )

        return {**first, "data": items}

    @staticmethod
    def _page_params(page_number: int) -> dict[str, int]:
        """The query for one page of a collection.

        The parameter names carry literal brackets, as JSON:API spells them and
        as they were verified live. ``requests`` percent-encodes the brackets on
        the wire -- ``page%5Bsize%5D`` -- and does so whether they are passed here
        or written into the URL string by hand, so there is no way to send the
        unencoded form from this client. Staging decodes them: encoded and
        literal-bracket requests were checked live and return identical results.
        """
        return {"page[size]": PAGE_SIZE, "page[number]": page_number}

    @staticmethod
    def _total_records(document: dict[str, Any]) -> int | None:
        """The collection's ``meta.total-records``, or None if it is absent or unusable."""
        meta = document.get("meta")
        if not isinstance(meta, dict):
            return None
        total = meta.get("total-records")
        return total if isinstance(total, int) and not isinstance(total, bool) else None

    @staticmethod
    def _resource_key(resource: Any) -> tuple[str, str] | None:
        """A resource's ``(type, id)`` identity, or None when it has no id to key on.

        Paging dedupes on this so a server that repeats a page, or one whose
        collection shifts under a concurrent insert, cannot inflate the count and
        drive the loop past its own stopping condition. A resource with no id
        cannot be recognised as a repeat and is always kept.
        """
        if not isinstance(resource, dict):
            return None
        resource_id = resource.get("id")
        if resource_id is None:
            return None
        return str(resource.get("type", "")), str(resource_id)

    def _get_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET one URL and return its parsed JSON document."""
        response = self.session.get(url, params=params)
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.JSONDecodeError as e:
            body = response.text
            preview = body[:BODY_PREVIEW_CHARS]
            elided = f" (truncated from {len(body)} chars)" if len(body) > BODY_PREVIEW_CHARS else ""
            raise requests.exceptions.HTTPError(
                f"Failed to parse JSON response from {url}: HTTP {response.status_code}, "
                f"{len(response.content)} bytes, content-type "
                f"{response.headers.get('Content-Type', 'unknown')!r}. "
                f"Body preview: {preview!r}{elided}",
                response=response,
            ) from e

    def _delete(self, resource_type: str, item_id: str) -> None:
        """Delete a resource from the API."""
        url = f"{self.base_url}/{resource_type}/{item_id}"
        response = self.session.delete(url)
        response.raise_for_status()

    @staticmethod
    def write_payload(
        resource_type: str,
        attributes: dict[str, Any],
        object_id: str | None = None,
        relationships: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build the JSON:API document a create or update sends.

        Every write goes through here so the envelope is described once. That
        matters beyond tidiness: the attribute keys must be kebab-case, and when
        each method spelled its own payload a camelCase key slipped in and the
        server accepted it, returned 201 and silently discarded the value (#75).

        Args:
            resource_type: The JSON:API ``type``, e.g. ``"log-entries"``.
            attributes: Attribute members, keyed in kebab-case.
            object_id: The resource id, for an update.
            relationships: Relationship members, usually from :meth:`relationship`.

        Returns:
            dict: The ``{"data": ...}`` document to send as the request body.
        """
        data: dict[str, Any] = {"type": resource_type}
        if object_id is not None:
            data["id"] = object_id
        data["attributes"] = attributes
        if relationships:
            data["relationships"] = relationships
        return {"data": data}

    @staticmethod
    def relationship(resource_type: str, object_id: str) -> dict[str, Any]:
        """Build one JSON:API relationship member pointing at a resource."""
        return {"data": {"type": resource_type, "id": object_id}}

    @staticmethod
    def entity_data(resource: dict[str, Any]) -> dict[str, Any]:
        """Build the dict a model validates from: wire attributes plus id/type.

        Attributes arrive kebab-case and are matched by each model's alias
        generator. id and type come from the JSON:API resource level, where they
        always appear, and override any same-named attribute.
        """
        attrs = dict(resource.get("attributes", {}))
        attrs["id"] = str(resource.get("id", ""))
        attrs["type"] = resource.get("type", "")
        return attrs

    @staticmethod
    def relationship_id(resource: dict[str, Any], name: str) -> str:
        """Return the id of a JSON:API relationship, or '' if absent."""
        data = resource.get("relationships", {}).get(name, {}).get("data", {})
        return str(data.get("id", "")) if data else ""

    def _parse_campaign(self, resource: dict[str, Any]) -> Campaign:
        camp = Campaign.model_validate(self.entity_data(resource))
        camp._client = self
        return camp

    def _parse_log(self, resource: dict[str, Any]) -> Log:
        log_obj = Log.model_validate(self.entity_data(resource))
        # The wire log payload carries no campaign-id attribute; it comes from
        # the relationships block. Fall back to it when the attribute is absent.
        if not log_obj.campaign_id:
            log_obj.campaign_id = self.relationship_id(resource, "campaign")
        log_obj._client = self
        return log_obj

    def _parse_log_entry(self, resource: dict[str, Any]) -> LogEntry:
        entry = LogEntry.model_validate(self.entity_data(resource))
        if not entry.log_id:
            entry.log_id = self.relationship_id(resource, "log")
        entry._client = self
        return entry

    def _parse_player_log(self, resource: dict[str, Any]) -> PlayerLog:
        log_obj = PlayerLog.model_validate(self.entity_data(resource))
        if not log_obj.campaign_id:
            log_obj.campaign_id = self.relationship_id(resource, "campaign")
        log_obj._client = self
        return log_obj

    def _parse_player_log_entry(self, resource: dict[str, Any]) -> PlayerLogEntry:
        entry = PlayerLogEntry.model_validate(self.entity_data(resource))
        if not entry.log_id:
            entry.log_id = (
                self.relationship_id(resource, "player-log")
                or self.relationship_id(resource, "playerLog")
                or self.relationship_id(resource, "log")
            )
        entry._client = self
        return entry

    def _parse_campaign_entry(self, resource: dict[str, Any]) -> CampaignEntry:
        entry = CampaignEntry.model_validate(self.entity_data(resource))
        # The raw-public fallback lives on CampaignEntry.text, so raw_text keeps
        # reporting what the server actually sent rather than a parse-time guess.
        if not entry.campaign_id:
            entry.campaign_id = self.relationship_id(resource, "campaign")
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
        payload = self.write_payload("campaigns", {"title": title, "description": description})
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

        payload = self.write_payload("campaigns", attributes, object_id=campaign_id)
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
        payload = self.write_payload(
            "logs",
            {"title": title, "description": description, "campaign-id": campaign_id},
            relationships={"campaign": self.relationship("campaigns", campaign_id)},
        )
        response = self.session.post(url, json=payload, timeout=30)
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

        payload = self.write_payload("logs", attributes, object_id=log_id)
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
        payload = self.write_payload(
            "log-entries",
            {"raw-text": raw_text, "log-id": log_id},
            relationships={"log": self.relationship("logs", log_id)},
        )
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
        payload = self.write_payload("log-entries", {"raw-text": raw_text}, object_id=entry_id)
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
        payload = self.write_payload(
            "campaign-entries",
            {"raw-text": raw_text, "campaign-id": campaign_id},
            relationships={"campaign": self.relationship("campaigns", campaign_id)},
        )
        response = self.session.post(url, json=payload, timeout=30)
        response.raise_for_status()
        json_resp = response.json()
        data = json_resp.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_campaign_entry(data)

    def update_campaign_entry(self, entry_id: str, raw_text: str) -> CampaignEntry:
        """Update the text content of an existing campaign entry (page)."""
        url = f"{self.base_url}/campaign-entries/{entry_id}"
        payload = self.write_payload("campaign-entries", {"raw-text": raw_text}, object_id=entry_id)
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

    # --- Player Logs ---
    def get_player_logs(self) -> list[PlayerLog]:
        """Retrieve all player logs available across the user's campaigns."""
        response = self._get("player-logs")
        data = response.get("data", [])
        if not isinstance(data, list):
            data = [data]
        return [self._parse_player_log(r) for r in data]

    def get_player_log(self, log_id: str) -> PlayerLog:
        """Retrieve a specific player log by its unique identifier."""
        response = self._get("player-logs", log_id)
        data = response.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_player_log(data)

    def create_player_log(self, campaign_id: str, title: str, description: str = "") -> PlayerLog:
        """Create a new child player log attached to a specific campaign."""
        url = f"{self.base_url}/player-logs"
        payload = self.write_payload(
            "player-logs",
            {"title": title, "description": description, "campaign-id": campaign_id},
            relationships={"campaign": self.relationship("campaigns", campaign_id)},
        )
        response = self.session.post(url, json=payload, timeout=30)
        response.raise_for_status()
        json_resp = response.json()
        data = json_resp.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_player_log(data)

    def update_player_log(self, log_id: str, title: str | None = None, description: str | None = None) -> PlayerLog:
        """Update the metadata (title or description) of an existing player log."""
        url = f"{self.base_url}/player-logs/{log_id}"
        attributes: dict[str, Any] = {}
        if title is not None:
            attributes["title"] = title
        if description is not None:
            attributes["description"] = description

        payload = self.write_payload("player-logs", attributes, object_id=log_id)
        response = self.session.patch(url, json=payload, timeout=30)
        response.raise_for_status()
        json_resp = response.json()
        data = json_resp.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_player_log(data)

    def delete_player_log(self, log_id: str) -> None:
        """Permanently delete a player log and its associated entries."""
        self._delete("player-logs", log_id)

    # --- Player Log Entries ---
    def get_player_log_entries(self, log_id: str | None = None) -> list[PlayerLogEntry]:
        """Retrieve all individual player log entries across the user's player logs."""
        response = self._get("player-log-entries")
        data = response.get("data", [])
        if not isinstance(data, list):
            data = [data]
        entries = [self._parse_player_log_entry(r) for r in data]
        if log_id:
            entries = [e for e in entries if e.log_id == log_id]
        return entries

    def get_player_log_entry(self, entry_id: str) -> PlayerLogEntry:
        """Retrieve a specific player log entry by its unique identifier."""
        response = self._get("player-log-entries", entry_id)
        data = response.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_player_log_entry(data)

    def create_player_log_entry(self, log_id: str, raw_text: str) -> PlayerLogEntry:
        """Create a new text entry attached to a specific player log."""
        url = f"{self.base_url}/player-log-entries"
        # The relationship member is "player-log", like every other wire name.
        # "playerLog" and "log" are both accepted with 201 and silently leave the
        # entry orphaned, so this spelling is load-bearing. Verified live.
        payload = self.write_payload(
            "player-log-entries",
            {"raw-text": raw_text, "log-id": log_id},
            relationships={"player-log": self.relationship("player-logs", log_id)},
        )
        response = self.session.post(url, json=payload, timeout=30)
        response.raise_for_status()
        json_resp = response.json()
        data = json_resp.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_player_log_entry(data)

    def update_player_log_entry(self, entry_id: str, raw_text: str) -> PlayerLogEntry:
        """Update the textual content of an existing player log entry."""
        url = f"{self.base_url}/player-log-entries/{entry_id}"
        payload = self.write_payload("player-log-entries", {"raw-text": raw_text}, object_id=entry_id)
        response = self.session.patch(url, json=payload, timeout=30)
        response.raise_for_status()
        json_resp = response.json()
        data = json_resp.get("data", {})
        if isinstance(data, list):
            raise ValueError("Expected a single resource, got a list.")
        return self._parse_player_log_entry(data)

    def delete_player_log_entry(self, entry_id: str) -> None:
        """Permanently delete a specific player log entry."""
        self._delete("player-log-entries", entry_id)
