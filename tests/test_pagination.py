"""``LoggerClient._get`` walks a paged collection to completion (issue #77).

The API pages and reports ``meta.total-records`` on every top-level listing, so
a truncated read is detectable. ``_get`` used to issue one request and return
whatever came back, which meant a collection larger than a page came back short
with nothing to say so.

Every test here is mocked. The payloads come from ``wire``, so the keys are the
kebab-case the server really sends -- ``total-records``, not ``totalRecords``.
No test makes a live request.
"""

import pytest
import requests_mock
import wire

from campaign_logger.api import MAX_PAGE_REQUESTS
from campaign_logger.api import PAGE_SIZE
from campaign_logger.api import LoggerClient
from campaign_logger.api import PaginationError

BASE_URL = "https://logger-staging.campaign-logger.com"


@pytest.fixture
def client():
    return LoggerClient(base_url=BASE_URL, client_id="test_id", client_secret="test_secret")


def paging_server(total, resource_type="log-entries"):
    """A requests_mock ``json`` callback that serves ``total`` records, page by page.

    It honours whatever ``page[size]`` and ``page[number]`` the client sends and
    reports ``meta.total-records``, the way staging does.
    """

    def respond(request, context):
        size = int(request.qs["page[size]"][0])
        number = int(request.qs["page[number]"][0])
        start = (number - 1) * size
        ids = [f"e{i}" for i in range(start, min(start + size, total))]
        return wire.page(resource_type, ids, total_records=total, attributes={"raw-text": "text"})

    return respond


def test_multi_page_collection_is_fetched_fully_and_in_order(client):
    """Every page is requested and the resources are concatenated in page order."""
    total = PAGE_SIZE * 2 + 3
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/log-entries", json=paging_server(total))
        result = client._get("log-entries")

    data = result["data"]
    assert len(data) == total  # nosec
    assert [r["id"] for r in data] == [f"e{i}" for i in range(total)]  # nosec
    assert m.call_count == 3  # nosec
    # The paging query goes out from the very first request. requests sends the
    # brackets percent-encoded, which is what the server has to decode.
    assert [r.qs["page[number]"][0] for r in m.request_history] == ["1", "2", "3"]  # nosec
    assert all(r.qs["page[size]"][0] == str(PAGE_SIZE) for r in m.request_history)  # nosec
    assert all("page%5Bsize%5D=" in r.url for r in m.request_history)  # nosec
    # The envelope is unchanged apart from data, so meta still reports the total.
    assert result["meta"] == {"total-records": total}  # nosec


def test_single_page_collection_costs_exactly_one_request(client):
    """A collection that fits in one page does not pay for a second request."""
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaigns", json=wire.page("campaigns", ["c1", "c2", "c3"], total_records=3, attributes={"title": "A"}))
        result = client._get("campaigns")

    assert len(result["data"]) == 3  # nosec
    assert m.call_count == 1  # nosec


def test_response_without_meta_is_returned_as_is(client):
    """A related-resource route sends no ``meta``, so it is returned unpaged.

    There is no total to compare against, so paging would be guesswork; the
    response comes back exactly as it arrived, at the cost of one request.
    """
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaigns/c1/logs", json=wire.collection("logs", ("l1", {"title": "A"}), ("l2", {"title": "B"})))
        result = client._get("campaigns/c1/logs")

    assert [r["id"] for r in result["data"]] == ["l1", "l2"]  # nosec
    assert "meta" not in result  # nosec
    assert m.call_count == 1  # nosec


def test_meta_without_a_usable_total_is_returned_as_is(client):
    """A ``meta`` block with no integer ``total-records`` is treated as no total."""
    document = wire.page("log-entries", ["e1"], attributes={"raw-text": "text"})
    document["meta"] = {"total-records": "many"}
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/log-entries", json=document)
        result = client._get("log-entries")

    assert len(result["data"]) == 1  # nosec
    assert m.call_count == 1  # nosec


def test_single_resource_get_is_not_paginated(client):
    """A GET by id returns its object untouched and sends no paging query."""
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaigns/c1", json=wire.document("campaigns", "c1", title="My Campaign"))
        result = client._get("campaigns", "c1")

    assert result["data"]["id"] == "c1"  # nosec
    assert isinstance(result["data"], dict)  # nosec
    assert m.call_count == 1  # nosec
    assert m.request_history[0].qs == {}  # nosec


def test_a_repeating_page_stops_instead_of_spinning(client):
    """A server that keeps returning the same page is stopped on the second page.

    The records are deduplicated on ``(type, id)``, so the repeat adds nothing,
    the loop gives up immediately and says the result is incomplete rather than
    requesting the same page until the cap.
    """
    stuck = wire.page("log-entries", [f"e{i}" for i in range(PAGE_SIZE)], total_records=PAGE_SIZE * 10)
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/log-entries", json=stuck)
        with pytest.warns(UserWarning, match="returned nothing new"):
            result = client._get("log-entries")

    assert len(result["data"]) == PAGE_SIZE  # nosec
    assert m.call_count == 2  # nosec


def test_incomplete_warning_points_at_the_callers_code(client):
    """The incomplete-collection warning names the line that called the public method.

    Pointing inside ``api.py`` would tell the reader nothing about which of their
    reads came back short.
    """
    stuck = wire.page("log-entries", [f"e{i}" for i in range(PAGE_SIZE)], total_records=PAGE_SIZE * 10)
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/log-entries", json=stuck)
        with pytest.warns(UserWarning, match="returned nothing new") as record:
            client.get_log_entries()

    assert record[0].filename == __file__  # nosec


def short_server(available, promised):
    """A server promising ``promised`` records but only able to serve ``available``."""

    def respond(request, context):
        size = int(request.qs["page[size]"][0])
        number = int(request.qs["page[number]"][0])
        start = (number - 1) * size
        ids = [f"e{i}" for i in range(start, min(start + size, available))]
        return wire.page("log-entries", ids, total_records=promised)

    return respond


def test_a_collection_that_runs_out_early_warns_and_returns_what_arrived(client):
    """``total-records`` above what the server can actually serve stops cleanly.

    Records deleted between requests leave the promised total unreachable. That
    is the server's race, not a client bug, so the partial collection is
    returned with a warning rather than an exception.
    """
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/log-entries", json=short_server(PAGE_SIZE + 2, PAGE_SIZE * 3))
        with pytest.warns(UserWarning, match=r"stopped at \d+ of"):
            result = client._get("log-entries")

    assert len(result["data"]) == PAGE_SIZE + 2  # nosec
    assert m.call_count == 3  # nosec


def test_request_cap_raises_when_the_collection_never_completes(client):
    """A collection that never reports complete raises instead of running forever."""
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/log-entries", json=paging_server(PAGE_SIZE * (MAX_PAGE_REQUESTS + 10)))
        with pytest.raises(PaginationError, match=f"{MAX_PAGE_REQUESTS}-request cap"):
            client._get("log-entries")

    assert m.call_count == MAX_PAGE_REQUESTS  # nosec


def test_resources_without_ids_are_never_deduplicated(client):
    """Pages are only deduplicated where there is an id to recognise a repeat by.

    The server always sends ids, and a malformed member is not something it does
    either -- but the identity helper is what protects the loop, so it must cope
    with both rather than drop records or raise.
    """
    pages = [
        {"data": [{"type": "log-entries", "attributes": {}}, "not-a-resource"], "meta": {"total-records": 4}},
        {"data": [{"type": "log-entries", "attributes": {}}, {"type": "log-entries", "attributes": {}}], "meta": {"total-records": 4}},
    ]
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/log-entries", [{"json": p} for p in pages])
        result = client._get("log-entries")

    assert len(result["data"]) == 4  # nosec
    assert m.call_count == 2  # nosec


def test_public_listing_returns_every_page(client):
    """The paging is invisible to callers: ``get_log_entries`` returns all pages.

    The return shape is unchanged, so the parsers, the CLI and the MCP server
    need no adjustment -- they simply stop seeing a truncated list.
    """
    total = PAGE_SIZE + 4
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/log-entries", json=paging_server(total))
        entries = client.get_log_entries()

    assert len(entries) == total  # nosec
    assert entries[-1].id == f"e{total - 1}"  # nosec
    assert m.call_count == 2  # nosec
