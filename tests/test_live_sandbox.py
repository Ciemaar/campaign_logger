"""Mocked tests for G3 (sacrificial container) and G4 (created ledger).

As with the G2 tests, the refusal paths carry the weight: a preflight that
accepts anything is worse than none, because it looks like protection. Issue
#62 section 12 step 8 asks specifically for the refusal paths to be tested --
unset variables, a title that disagrees with the id, and a target equal to
``CL_DEFAULT_CAMPAIGN_ID``.

Nothing here touches the network.
"""

import json

import pytest
from live_guard import DELETE
from live_guard import WRITE
from live_guard import HttpEffectGuard
from live_guard import LiveGuardViolation
from live_sandbox import CreatedLedger
from live_sandbox import SandboxConfig
from live_sandbox import SandboxConfigError
from live_sandbox import load_sandbox_config
from live_sandbox import make_ledger_predicate
from live_sandbox import make_sacrificial_predicate
from live_sandbox import preflight

SANDBOX_ID = "f" * 32
OTHER_ID = "a" * 32
CREATED_LOG_ID = "b" * 32
TITLE = "PYTEST-LIVE-sandbox"
LOGGER = "https://logger.campaign-logger.com"

GOOD_ENV = {
    "CL_LIVE_SACRIFICIAL_CAMPAIGN_ID": SANDBOX_ID,
    "CL_LIVE_SACRIFICIAL_CAMPAIGN_TITLE": TITLE,
}


class FakeCampaign:
    """A campaign with just the attribute preflight reads."""

    def __init__(self, title):
        """Hold the title the fake server will report."""
        self.title = title


class FakeClient:
    """Minimal stand-in for LoggerClient.get_campaign."""

    def __init__(self, title):
        """Serve one campaign with ``title`` for any id requested."""
        self._campaign = FakeCampaign(title)
        self.requested = []

    def get_campaign(self, campaign_id):
        """Record the lookup and return the fixed campaign."""
        self.requested.append(campaign_id)
        return self._campaign


def config():
    return SandboxConfig(SANDBOX_ID, TITLE)


# --- G3: configuration refusal paths -----------------------------------------


@pytest.mark.parametrize("missing", ["CL_LIVE_SACRIFICIAL_CAMPAIGN_ID", "CL_LIVE_SACRIFICIAL_CAMPAIGN_TITLE"])
def test_unset_variable_fails_rather_than_skips(missing):
    """A misconfigured write run must be loud; a skip would look like a pass."""
    env = dict(GOOD_ENV)
    del env[missing]
    with pytest.raises(SandboxConfigError, match=missing):
        load_sandbox_config(env)


@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_variable_is_treated_as_unset(blank):
    env = dict(GOOD_ENV, CL_LIVE_SACRIFICIAL_CAMPAIGN_ID=blank)
    with pytest.raises(SandboxConfigError, match="CL_LIVE_SACRIFICIAL_CAMPAIGN_ID"):
        load_sandbox_config(env)


@pytest.mark.parametrize("bad_id", ["not-an-id", "F" * 32, "f" * 31, "f" * 33, "../campaigns"])
def test_malformed_id_refused(bad_id):
    env = dict(GOOD_ENV, CL_LIVE_SACRIFICIAL_CAMPAIGN_ID=bad_id)
    with pytest.raises(SandboxConfigError, match="32 lowercase hex"):
        load_sandbox_config(env)


def test_title_without_the_prefix_refused():
    """The container must be *named* as sacrificial, not merely pointed at."""
    env = dict(GOOD_ENV, CL_LIVE_SACRIFICIAL_CAMPAIGN_TITLE="Curse of Strahd")
    with pytest.raises(SandboxConfigError, match="does not start with"):
        load_sandbox_config(env)


@pytest.mark.parametrize("var", ["CL_DEFAULT_CAMPAIGN_ID", "CL_DEFAULT_LOG_ID"])
def test_everyday_default_may_not_be_the_write_target(var):
    env = dict(GOOD_ENV, **{var: SANDBOX_ID})
    with pytest.raises(SandboxConfigError, match=var):
        load_sandbox_config(env)


def test_valid_configuration_loads():
    loaded = load_sandbox_config(dict(GOOD_ENV, CL_DEFAULT_CAMPAIGN_ID=OTHER_ID))
    assert loaded.campaign_id == SANDBOX_ID  # nosec
    assert loaded.title == TITLE  # nosec
    assert loaded.stamp("session-1") == "PYTEST-LIVE-session-1"  # nosec


def test_custom_prefix_is_honoured():
    env = {
        "CL_LIVE_SACRIFICIAL_CAMPAIGN_ID": SANDBOX_ID,
        "CL_LIVE_SACRIFICIAL_CAMPAIGN_TITLE": "SANDBOX-one",
        "CL_LIVE_OBJECT_PREFIX": "SANDBOX-",
    }
    assert load_sandbox_config(env).object_prefix == "SANDBOX-"  # nosec


# --- G3: preflight -----------------------------------------------------------


def test_preflight_rejects_a_title_that_disagrees_with_the_id():
    """A typo'd id that resolves to a real campaign fails here."""
    client = FakeClient("Curse of Strahd")
    with pytest.raises(SandboxConfigError, match="not 'PYTEST-LIVE-sandbox'"):
        preflight(client, config())
    assert client.requested == [SANDBOX_ID]  # nosec


def test_preflight_accepts_an_exact_title_match():
    assert preflight(FakeClient(TITLE), config()).title == TITLE  # nosec


@pytest.mark.parametrize("near_miss", ["PYTEST-LIVE-sandbox ", "pytest-live-sandbox", "PYTEST-LIVE-sandbox2"])
def test_preflight_requires_an_exact_match_not_a_near_one(near_miss):
    with pytest.raises(SandboxConfigError):
        preflight(FakeClient(near_miss), config())


# --- G4: the ledger ----------------------------------------------------------


def test_ledger_records_and_contains():
    ledger = CreatedLedger(config())
    ledger.record("logs", CREATED_LOG_ID)
    assert CREATED_LOG_ID in ledger  # nosec
    assert OTHER_ID not in ledger  # nosec
    assert ledger.ids() == [CREATED_LOG_ID]  # nosec


def test_ledger_refuses_to_record_a_malformed_id():
    ledger = CreatedLedger(config())
    with pytest.raises(SandboxConfigError, match="not the expected id shape"):
        ledger.record("logs", "")


def test_unrecorded_id_is_never_deletable():
    ledger = CreatedLedger(config())
    assert ledger.deletable(OTHER_ID) is False  # nosec
    assert ledger.leaked == [(OTHER_ID, "not recorded by this run")]  # nosec


def test_object_that_lost_our_prefix_is_leaked_not_deleted():
    """Leaking a stray test object is trivial; deleting the wrong one is not."""
    ledger = CreatedLedger(config())
    ledger.record("logs", CREATED_LOG_ID)

    class Renamed:
        title = "Session 14 - the real one"

    assert ledger.deletable(CREATED_LOG_ID, fetched=Renamed()) is False  # nosec
    assert ledger.leaked == [(CREATED_LOG_ID, "no longer carries the run prefix")]  # nosec


def test_object_still_carrying_our_prefix_is_deletable():
    ledger = CreatedLedger(config())
    ledger.record("logs", CREATED_LOG_ID)

    class Ours:
        title = "PYTEST-LIVE-session-1"

    assert ledger.deletable(CREATED_LOG_ID, fetched=Ours()) is True  # nosec
    assert ledger.leaked == []  # nosec


def test_raw_text_also_counts_as_carrying_the_prefix():
    ledger = CreatedLedger(config())
    ledger.record("campaign-entries", CREATED_LOG_ID)

    class Entry:
        raw_text = "PYTEST-LIVE-page body"

    assert ledger.deletable(CREATED_LOG_ID, fetched=Entry()) is True  # nosec


# --- the predicates, wired into the guard ------------------------------------


def guard_for(phase, ledger):
    cfg = ledger.config
    return HttpEffectGuard(
        phase,
        is_sacrificial_target=make_sacrificial_predicate(cfg, ledger),
        is_ledger_id=make_ledger_predicate(ledger),
    )


def create_log_body(campaign_id):
    """The payload api.py's create_log actually sends."""
    return json.dumps(
        {
            "data": {
                "type": "logs",
                "attributes": {"title": "PYTEST-LIVE-s1", "description": "", "campaignId": campaign_id},
                "relationships": {"campaign": {"data": {"type": "campaigns", "id": campaign_id}}},
            }
        }
    )


def test_create_into_the_sandbox_is_allowed():
    guard = guard_for(WRITE, CreatedLedger(config()))
    guard.check("POST", f"{LOGGER}/logs", create_log_body(SANDBOX_ID))


def test_create_at_the_account_root_is_refused():
    """The URL is identical to the allowed case; only the body differs.

    This is the case a URL-only predicate cannot see, and it is exactly what
    section 1.2 describes the existing e2e test doing.
    """
    guard = guard_for(WRITE, CreatedLedger(config()))
    with pytest.raises(LiveGuardViolation, match="does not resolve into the sacrificial campaign"):
        guard.check("POST", f"{LOGGER}/logs", create_log_body(OTHER_ID))


def test_create_with_no_body_is_refused():
    """Undetermined target means refused, never allowed."""
    guard = guard_for(WRITE, CreatedLedger(config()))
    with pytest.raises(LiveGuardViolation):
        guard.check("POST", f"{LOGGER}/logs", None)


def test_create_with_an_unparseable_body_is_refused():
    guard = guard_for(WRITE, CreatedLedger(config()))
    with pytest.raises(LiveGuardViolation):
        guard.check("POST", f"{LOGGER}/logs", b"\xff\xfe not json")


def test_body_naming_two_campaigns_is_refused_unless_both_are_ours():
    guard = guard_for(WRITE, CreatedLedger(config()))
    body = json.dumps({"data": [{"campaignId": SANDBOX_ID}, {"campaignId": OTHER_ID}]})
    with pytest.raises(LiveGuardViolation):
        guard.check("POST", f"{LOGGER}/logs", body)


def test_patch_of_the_sandbox_campaign_itself_is_allowed():
    guard = guard_for(WRITE, CreatedLedger(config()))
    guard.check("PATCH", f"{LOGGER}/campaigns/{SANDBOX_ID}", None)


def test_patch_of_another_campaign_is_refused_even_if_the_body_names_ours():
    """The URL wins: a body naming the sandbox must not launder a foreign URL."""
    guard = guard_for(WRITE, CreatedLedger(config()))
    with pytest.raises(LiveGuardViolation):
        guard.check("PATCH", f"{LOGGER}/campaigns/{OTHER_ID}", create_log_body(SANDBOX_ID))


def test_entry_under_a_log_we_created_is_allowed():
    ledger = CreatedLedger(config())
    ledger.record("logs", CREATED_LOG_ID)
    guard = guard_for(WRITE, ledger)
    body = json.dumps({"data": {"attributes": {"rawText": "PYTEST-LIVE-x", "logId": CREATED_LOG_ID}}})
    guard.check("POST", f"{LOGGER}/log-entries", body)


def test_entry_under_a_log_we_did_not_create_is_refused():
    guard = guard_for(WRITE, CreatedLedger(config()))
    body = json.dumps({"data": {"attributes": {"rawText": "x", "logId": OTHER_ID}}})
    with pytest.raises(LiveGuardViolation):
        guard.check("POST", f"{LOGGER}/log-entries", body)


def test_delete_is_confined_to_ledger_ids():
    ledger = CreatedLedger(config())
    ledger.record("logs", CREATED_LOG_ID)
    guard = guard_for(DELETE, ledger)

    guard.check("DELETE", f"{LOGGER}/logs/{CREATED_LOG_ID}")
    with pytest.raises(LiveGuardViolation, match="did not create"):
        guard.check("DELETE", f"{LOGGER}/campaigns/{SANDBOX_ID}")


def test_the_sandbox_campaign_itself_is_never_deletable():
    """The container is created by hand and outlives every run."""
    ledger = CreatedLedger(config())
    guard = guard_for(DELETE, ledger)
    with pytest.raises(LiveGuardViolation):
        guard.check("DELETE", f"{LOGGER}/campaigns/{SANDBOX_ID}")
