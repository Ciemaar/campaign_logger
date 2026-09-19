"""Builders for JSON:API payloads shaped like the ones the server really sends.

Mocks that return only the two or three attributes a test asserts on are how a
whole class of bug reaches production: the audit-trail fields were missing from
every mock, so nothing exercised the `datetime` parsing or the
`json.dumps(to_dict())` path in `cli.py`, and adding datetime fields broke the
CLI without a single test failing.

Attribute keys here are kebab-case, matching the wire (see
docs/live_testing_evidence.md). Values are shaped after a real staging response.
"""

from typing import Any

#: The audit/soft-delete/revision block every resource carries.
AUDIT_ATTRIBUTES: dict[str, Any] = {
    "created-on": "2026-09-16T02:26:10.416000",
    "updated-on": "2026-09-16T02:26:10.720990",
    "deleted-on": "",
    "is-deleted": False,
    "revision": "7ac376fe32bf42d6862f05743f75231b",
    "previous-revision": None,
    "string-id": None,
    "user-id": "cd0f000000000000000000000000FAKE",
}


def attributes(**overrides: Any) -> dict[str, Any]:
    """The audit block plus whatever the test cares about."""
    return {**AUDIT_ATTRIBUTES, **overrides}


def resource(resource_type: str, resource_id: str, **attrs: Any) -> dict[str, Any]:
    """A single JSON:API resource object, audit fields included."""
    return {"id": resource_id, "type": resource_type, "attributes": attributes(**attrs)}


def document(resource_type: str, resource_id: str, **attrs: Any) -> dict[str, Any]:
    """A JSON:API document wrapping one resource: ``{"data": {...}}``."""
    return {"data": resource(resource_type, resource_id, **attrs)}


def collection(
    resource_type: str,
    *ids_and_attrs: tuple[str, dict[str, Any]],
    total_records: int | None = None,
) -> dict[str, Any]:
    """A JSON:API document wrapping a list of resources.

    Args:
        resource_type: The JSON:API ``type`` every resource carries.
        ids_and_attrs: One ``(id, attributes)`` pair per resource.
        total_records: The ``meta.total-records`` a top-level listing sends. Pass
            it whenever the test is about paging; leave it out to mimic a
            related-resource route, which sends no ``meta`` block at all (#77).
    """
    document: dict[str, Any] = {"data": [resource(resource_type, rid, **attrs) for rid, attrs in ids_and_attrs]}
    if total_records is not None:
        document["meta"] = {"total-records": total_records}
    return document


def page(
    resource_type: str,
    ids: list[str],
    total_records: int | None = None,
    **attrs: Any,
) -> dict[str, Any]:
    """One page of a listing: ``ids`` as resources, plus ``meta.total-records``.

    The shorthand for a paging test, where the ids matter and the attributes do
    not vary from one resource to the next.
    """
    return collection(resource_type, *((rid, dict(attrs)) for rid in ids), total_records=total_records)


def realistic_campaign(campaign_id: str = "c1", title: str = "A Campaign") -> dict[str, Any]:
    """A campaign resource as the server sends it, audit fields included."""
    return resource("campaigns", campaign_id, title=title, description="", **{"image-url": ""})
