"""Phase 1 -- the live read-only suite (issue #62).

Safe to run whenever `--run-live-read` is passed and credentials are set. It
cannot damage anything: the guard is in READ phase, so a stray write raises
before it leaves the process. This is the cheapest way to learn what the server
actually returns, and it feeds the §5 capture that settles the wire-format
questions the swagger cannot answer (casing, pagination, sparse fieldsets).

Run against the staging sandbox:

    set -a; source .env.sandbox; set +a
    pytest tests/test_live_read.py --run-live-read
"""

import json
import pathlib
from typing import Any

import pytest

pytestmark = [pytest.mark.live_read, pytest.mark.timeout(60)]

#: Raw payloads land here for §5 analysis. Gitignored -- even on staging (which
#: holds separate data) captured bodies do not belong in git.
CAPTURES = pathlib.Path(".captures")


def _capture(client, name, path) -> tuple[int, Any]:
    """GET ``path`` through the guarded session and record the raw payload.

    Tolerant by design: a non-2xx is recorded, not raised, so the capture step
    documents what the server does rather than failing on the first surprise.
    Returns ``(status, payload_or_none)``.
    """
    CAPTURES.mkdir(exist_ok=True)
    response = client.session.get(f"{client.base_url}/{path}")
    record = {"path": path, "status": response.status_code, "content_type": response.headers.get("Content-Type")}
    try:
        record["body"] = response.json()
    except ValueError:
        record["body"] = None
        record["text_len"] = len(response.text)
    (CAPTURES / f"{name}.json").write_text(json.dumps(record, indent=2))
    return response.status_code, record.get("body")


# --- connectivity and identity -----------------------------------------------


def test_sandbox_campaign_is_listed(live_read_client, sandbox_config):
    campaigns = live_read_client.get_campaigns()
    assert isinstance(campaigns, list)  # nosec
    assert sandbox_config.campaign_id in {c.id for c in campaigns}  # nosec


def test_get_campaign_detail_matches_title(live_read_client, sandbox_config):
    campaign = live_read_client.get_campaign(sandbox_config.campaign_id)
    assert campaign.id == sandbox_config.campaign_id  # nosec
    assert campaign.title == sandbox_config.title  # nosec


# --- every listing endpoint returns a list (may be empty) --------------------


@pytest.mark.parametrize(
    "reader",
    ["get_campaigns", "get_logs", "get_log_entries", "get_campaign_entries", "get_player_logs", "get_player_log_entries"],
)
def test_listing_returns_a_list(live_read_client, reader):
    assert isinstance(getattr(live_read_client, reader)(), list)  # nosec


# --- §5 capture: real payloads for the wire-format questions ------------------


def test_capture_wire_payloads(live_read_client, sandbox_config):
    """Record real payloads and settle what can be settled from them.

    Casing (Q from §5): does the wire use camelCase like the swagger schemas
    and the mocks, or kebab-case like the 2022 fixtures?
    """
    status, campaigns = _capture(live_read_client, "campaigns", "campaigns")
    assert status == 200  # nosec
    _capture(live_read_client, "campaign-detail", f"campaigns/{sandbox_config.campaign_id}")
    for resource in ("logs", "log-entries", "campaign-entries", "player-logs", "player-log-entries"):
        _capture(live_read_client, resource, resource)

    # Inspect the attribute keys the server actually sent.
    data = campaigns.get("data") if isinstance(campaigns, dict) else None
    if isinstance(data, list):
        first = data[0] if data else {}
    elif isinstance(data, dict):
        first = data
    else:
        first = {}
    attributes = first.get("attributes") if isinstance(first, dict) else None
    attribute_keys = list(attributes.keys()) if isinstance(attributes, dict) else []
    assert attribute_keys, "no attributes in the campaigns payload to inspect"  # nosec

    has_camel = any(any(c.isupper() for c in k) for k in attribute_keys)
    has_kebab = any("-" in k for k in attribute_keys)
    # Record the verdict where the run's output shows it; do not assert a
    # specific casing, since that is precisely the open question.
    print(f"\n[casing] attribute keys: {sorted(attribute_keys)}")
    print(f"[casing] camelCase={has_camel} kebab-case={has_kebab}")


def test_pagination_signal_captured(live_read_client):
    """Record whether any listing paginates (§10 Q4).

    _get has no pagination handling, so if a listing pages, get_log_entries
    silently returns only the first page.

    JSON:API puts paging under top-level ``links`` / ``meta``. Record their
    presence rather than asserting, since the sandbox may be too small to page.
    """
    response = live_read_client.session.get(f"{live_read_client.base_url}/log-entries")
    assert response.status_code == 200  # nosec
    body = response.json()
    links = body.get("links", {}) if isinstance(body, dict) else {}
    meta = body.get("meta", {}) if isinstance(body, dict) else {}
    print(f"\n[pagination] links keys={sorted(links)} meta keys={sorted(meta)}")
    if "next" in links:
        print("[pagination] a 'next' link exists -- _get pages by page[number] against meta.total-records, not by links")
