"""G3 and G4 -- the sacrificial container and the created-object ledger.

G3 pins every write to one named campaign, verified two ways so that neither a
typo'd id nor a config copied from another machine can redirect writes at real
play data. G4 records what the run itself created, so cleanup can never name
anything else.

Both are configured from the environment rather than from flags, deliberately
and in contrast to G1: the *opt-in* must be typed per run (a flag), but the
*target* is a stable per-machine fact (an id), and an id baked into a test file
would be one account's data checked into a shared repository -- the mistake
section 1.3 of issue #62 records.

Failures here are :class:`SandboxConfigError`, never ``skip``. A write run that
is misconfigured must be loud: a silent skip looks like a pass.
"""

import json
import re
from urllib.parse import urlsplit

#: Prefix stamped on every object a live run creates, and required at the start
#: of the sacrificial campaign's own title so an ordinary campaign cannot be
#: pointed at by the variable.
DEFAULT_OBJECT_PREFIX = "PYTEST-LIVE-"

#: Observed id shape. Confirmed against the 2022 staging fixtures and the
#: sandbox campaign id; still only two accounts' worth of evidence, so section
#: 10 Q5 stays open and a non-matching id means *refuse*, never "delete anyway".
ID_SHAPE = re.compile(r"^[0-9a-f]{32}$")

#: Config that must not silently become a write target. ``cli.py`` reads these
#: from ``~/.campaign_logger.json``; the live suite never calls ``load_config``.
FORBIDDEN_TARGET_VARS = ("CL_DEFAULT_CAMPAIGN_ID", "CL_DEFAULT_LOG_ID")

#: Body keys that name the campaign a create is attached to. The wire format is
#: kebab-case; the snake_case spellings are kept for a body built by hand. A
#: camelCase key is deliberately absent: it is no longer emitted, and if one ever
#: reappeared the guard would fail to resolve the target and refuse the write,
#: which is the safe direction.
CAMPAIGN_KEYS = ("campaign-id", "campaign_id")

#: Body keys naming a parent that is itself an object, resolved via the ledger.
PARENT_KEYS = ("log-id", "log_id", "entry-id", "entry_id")


class SandboxConfigError(AssertionError):
    """The sacrificial campaign is missing, mis-specified, or unsafe."""


class SandboxConfig:
    """The verified identity of the one campaign writes may touch."""

    def __init__(self, campaign_id, title, object_prefix=DEFAULT_OBJECT_PREFIX):
        """Hold a checked id/title pair. Build via :func:`load_sandbox_config`."""
        self.campaign_id = campaign_id
        self.title = title
        self.object_prefix = object_prefix

    def stamp(self, name):
        """Prefix ``name`` so every created object is identifiable as ours."""
        return f"{self.object_prefix}{name}"


def load_sandbox_config(environ):
    """Read and validate the sacrificial-campaign configuration.

    Raises :class:`SandboxConfigError` unless every structural condition holds.
    This runs before any network call, so a misconfigured run fails without
    touching the account at all.
    """
    campaign_id = (environ.get("CL_LIVE_SACRIFICIAL_CAMPAIGN_ID") or "").strip()
    title = (environ.get("CL_LIVE_SACRIFICIAL_CAMPAIGN_TITLE") or "").strip()
    prefix = environ.get("CL_LIVE_OBJECT_PREFIX") or DEFAULT_OBJECT_PREFIX

    missing = [
        name
        for name, value in (
            ("CL_LIVE_SACRIFICIAL_CAMPAIGN_ID", campaign_id),
            ("CL_LIVE_SACRIFICIAL_CAMPAIGN_TITLE", title),
        )
        if not value
    ]
    if missing:
        raise SandboxConfigError(
            f"live write/delete phases need {' and '.join(missing)}. "
            "Refusing to run: without a verified container, writes would land at the account root."
        )

    if not ID_SHAPE.match(campaign_id):
        raise SandboxConfigError(
            f"CL_LIVE_SACRIFICIAL_CAMPAIGN_ID {campaign_id!r} is not 32 lowercase hex characters. "
            "Refusing rather than guessing what it addresses."
        )

    if not title.startswith(prefix):
        raise SandboxConfigError(
            f"CL_LIVE_SACRIFICIAL_CAMPAIGN_TITLE {title!r} does not start with {prefix!r}. "
            "The sacrificial campaign must be named as one, so an ordinary campaign cannot be pointed at."
        )

    for var in FORBIDDEN_TARGET_VARS:
        if (environ.get(var) or "").strip() == campaign_id:
            raise SandboxConfigError(
                f"{var} equals the sacrificial campaign id. Your everyday default and the write target must not be the same campaign."
            )

    return SandboxConfig(campaign_id, title, prefix)


def preflight(client, config):
    """Confirm the configured id really is the campaign the title claims.

    The second of G3's two checks, and the only one that needs the network: a
    typo'd id that happens to resolve to a real campaign passes the shape check
    but fails here, because its title will not match.
    """
    campaign = client.get_campaign(config.campaign_id)
    actual = getattr(campaign, "title", None)
    if actual != config.title:
        raise SandboxConfigError(
            f"campaign {config.campaign_id} is titled {actual!r}, not {config.title!r}. "
            "Refusing to write: the id and the title disagree, so one of them is wrong."
        )
    return campaign


class CreatedLedger:
    """Records every object this run created. Nothing else is ever deletable."""

    def __init__(self, config):
        """Start an empty ledger bound to a verified :class:`SandboxConfig`."""
        self.config = config
        self.entries = []
        #: Ids deliberately not deleted, for manual review. Leaking a stray test
        #: object is trivial; deleting the wrong object is not.
        self.leaked = []

    def record(self, resource_type, object_id):
        """Note an object at the moment it is created."""
        if not ID_SHAPE.match(object_id or ""):
            raise SandboxConfigError(f"refusing to record {resource_type} id {object_id!r}: not the expected id shape")
        self.entries.append((resource_type, object_id))
        return object_id

    def __contains__(self, object_id):
        """Whether this run created ``object_id``."""
        return any(recorded == object_id for _, recorded in self.entries)

    def ids(self):
        """Every recorded id, creation order preserved."""
        return [object_id for _, object_id in self.entries]

    def deletable(self, object_id, fetched=None):
        """Whether ``object_id`` may be deleted, re-validated at deletion time.

        ``fetched`` is the object as the server currently reports it. If it no
        longer carries our prefix it is not ours any more -- leak it and say so.
        """
        if object_id not in self:
            self.leaked.append((object_id, "not recorded by this run"))
            return False
        if not ID_SHAPE.match(object_id or ""):
            self.leaked.append((object_id, "id shape changed"))
            return False
        if fetched is not None and not self._looks_like_ours(fetched):
            self.leaked.append((object_id, "no longer carries the run prefix"))
            return False
        return True

    def _looks_like_ours(self, fetched):
        for attribute in ("title", "raw_text"):
            value = getattr(fetched, attribute, None)
            if isinstance(value, str) and value.startswith(self.config.object_prefix):
                return True
        return False


def _decode(body):
    """Best-effort JSON decode of a prepared request body."""
    if body is None:
        return None
    if isinstance(body, bytes):
        try:
            body = body.decode("utf-8")
        except UnicodeDecodeError:
            return None
    if isinstance(body, str):
        try:
            return json.loads(body)
        except ValueError:
            return None
    return body if isinstance(body, dict) else None


def _find_ids(payload, keys):
    """Collect every value under any of ``keys``, at any depth."""
    found = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in keys and isinstance(value, str):
                found.append(value)
            else:
                found.extend(_find_ids(value, keys))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_find_ids(item, keys))
    return found


def _campaign_ids_in(payload):
    """Campaign ids named anywhere in a write payload, attributes or relationships."""
    ids = list(_find_ids(payload, CAMPAIGN_KEYS))
    if isinstance(payload, dict):
        data = payload.get("data")
        relationships = data.get("relationships", {}) if isinstance(data, dict) else {}
        campaign = relationships.get("campaign", {}) if isinstance(relationships, dict) else {}
        related = campaign.get("data", {}) if isinstance(campaign, dict) else {}
        if isinstance(related, dict) and isinstance(related.get("id"), str):
            ids.append(related["id"])
    return ids


def make_sacrificial_predicate(config, ledger):
    """Build the ``(url, body) -> bool`` predicate G2 uses to gate writes.

    A write is permitted only when its target can be **positively resolved** to
    the sacrificial campaign. Three ways that can happen:

    1. the URL addresses the campaign itself, e.g. ``PATCH /campaigns/<id>``;
    2. the body names the campaign, which is how ``create_log`` and
       ``create_campaign_entry`` attach their object -- the URL there is the
       bare collection and says nothing about the target;
    3. the body names a parent (a log, an entry) that this run created, so the
       object is transitively inside the sandbox.

    Anything else is refused, including a write whose target simply cannot be
    determined. Undetermined means refused, never allowed.
    """

    def is_sacrificial_target(url, body=None):
        path = urlsplit(url).path
        segments = [segment for segment in path.split("/") if segment]

        # 1. The URL names an object: the campaign itself, or one we created.
        if segments:
            tail = segments[-1]
            if tail == config.campaign_id:
                return True
            if ID_SHAPE.match(tail) and tail in ledger:
                return True
            # An id in the URL that is neither ours nor the sandbox: refuse
            # without consulting the body, which could name the sandbox while
            # the URL points somewhere else entirely.
            if ID_SHAPE.match(tail):
                return False

        payload = _decode(body)
        if payload is None:
            return False

        # 2. The body names a campaign. Every campaign it names must be ours.
        campaign_ids = _campaign_ids_in(payload)
        if campaign_ids:
            return all(campaign_id == config.campaign_id for campaign_id in campaign_ids)

        # 3. The body names a parent object this run created.
        parent_ids = _find_ids(payload, PARENT_KEYS)
        if parent_ids:
            return all(parent_id in ledger for parent_id in parent_ids)

        return False

    return is_sacrificial_target


def make_ledger_predicate(ledger):
    """Build the ``url -> bool`` predicate G2 uses to gate deletes."""

    def is_ledger_id(url):
        segments = [segment for segment in urlsplit(url).path.split("/") if segment]
        if not segments:
            return False
        return segments[-1] in ledger

    return is_ledger_id
