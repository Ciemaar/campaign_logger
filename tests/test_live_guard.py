"""Mocked tests for G2's :class:`HttpEffectGuard` (issue #62 section 12, step 4).

The guard has to be tested before it is trusted, and its *refusal* paths matter
more than its permissive ones: a guard that silently allows everything passes
every happy-path test. Nothing here touches the network.
"""

import pytest
import requests
import requests_mock
from live_guard import DEFAULT_TIMEOUT
from live_guard import DELETE
from live_guard import READ
from live_guard import WRITE
from live_guard import HttpEffectGuard
from live_guard import LiveGuardViolation

LOGGER = "https://logger.campaign-logger.com"
GENERATOR = "https://generator.campaign-logger.com"
SACRIFICIAL = f"{LOGGER}/campaigns/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
REAL_CAMPAIGN = f"{LOGGER}/campaigns/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def sacrificial_only(url, body=None):
    return url.startswith(SACRIFICIAL)


def ledger_has(url):
    return url.endswith("cccccccccccccccccccccccccccccccc")


# --- refusal paths: the ones that actually protect the account ---------------


def test_read_phase_refuses_patch():
    guard = HttpEffectGuard(READ)
    with pytest.raises(LiveGuardViolation, match="attempts a write during the read-only phase"):
        guard.check("PATCH", REAL_CAMPAIGN)


def test_read_phase_refuses_post_and_delete():
    guard = HttpEffectGuard(READ)
    with pytest.raises(LiveGuardViolation):
        guard.check("POST", f"{LOGGER}/campaigns")
    with pytest.raises(LiveGuardViolation):
        guard.check("DELETE", REAL_CAMPAIGN)


def test_write_phase_refuses_delete():
    guard = HttpEffectGuard(WRITE, is_sacrificial_target=sacrificial_only)
    with pytest.raises(LiveGuardViolation, match="attempts a delete during the write phase"):
        guard.check("DELETE", SACRIFICIAL)


def test_write_phase_refuses_write_outside_sacrificial_campaign():
    guard = HttpEffectGuard(WRITE, is_sacrificial_target=sacrificial_only)
    with pytest.raises(LiveGuardViolation, match="does not resolve into the sacrificial campaign"):
        guard.check("PATCH", REAL_CAMPAIGN)


def test_delete_phase_refuses_id_not_in_ledger():
    guard = HttpEffectGuard(DELETE, is_ledger_id=ledger_has)
    with pytest.raises(LiveGuardViolation, match="did not create"):
        guard.check("DELETE", REAL_CAMPAIGN)


@pytest.mark.parametrize("phase", [READ, WRITE, DELETE])
@pytest.mark.parametrize(
    "url",
    [
        f"{LOGGER}/campaigns/",
        f"{LOGGER}/logs/",
        f"{LOGGER}/log-entries/",
        f"{LOGGER}/campaign-entries/",
        f"{LOGGER}/player-logs/",
    ],
)
def test_bare_collection_refused_in_every_phase(phase, url):
    """An empty id upstream must never reach the wire, whatever the phase."""
    guard = HttpEffectGuard(phase, is_sacrificial_target=lambda u, b=None: True, is_ledger_id=lambda u: True)
    with pytest.raises(LiveGuardViolation, match="empty id"):
        guard.check("DELETE", url)
    with pytest.raises(LiveGuardViolation, match="empty id"):
        guard.check("GET", url)


@pytest.mark.parametrize("phase", [READ, WRITE, DELETE])
@pytest.mark.parametrize("endpoint", ["validate", "generate"])
def test_generator_posts_refused_unless_their_own_flag_is_given(phase, endpoint):
    """No phase implies --run-live-generators, not even delete."""
    guard = HttpEffectGuard(phase, is_sacrificial_target=lambda u, b=None: True, is_ledger_id=lambda u: True)
    with pytest.raises(LiveGuardViolation, match="--run-live-generators"):
        guard.check("POST", f"{GENERATOR}/api2/generators/{endpoint}")


def test_generator_opt_in_grants_no_phase():
    """The capability is orthogonal: it must not unlock writes or deletes."""
    guard = HttpEffectGuard(READ, allow_generator_posts=True)
    with pytest.raises(LiveGuardViolation, match="attempts a write during the read-only phase"):
        guard.check("POST", f"{LOGGER}/campaigns")
    with pytest.raises(LiveGuardViolation):
        guard.check("DELETE", REAL_CAMPAIGN)


def test_unknown_method_refused():
    guard = HttpEffectGuard(DELETE, is_sacrificial_target=lambda u, b=None: True, is_ledger_id=lambda u: True)
    with pytest.raises(LiveGuardViolation, match="not permitted in any phase"):
        guard.check("HEAD", REAL_CAMPAIGN)


def test_predicates_default_to_refusing():
    """G3/G4 absent means refuse, not allow."""
    with pytest.raises(LiveGuardViolation):
        HttpEffectGuard(WRITE).check("POST", SACRIFICIAL)
    with pytest.raises(LiveGuardViolation):
        HttpEffectGuard(DELETE).check("DELETE", SACRIFICIAL)


def test_unknown_phase_rejected():
    with pytest.raises(ValueError, match="unknown phase"):
        HttpEffectGuard("readonly")


# --- permitted paths ---------------------------------------------------------


def test_read_phase_allows_get():
    guard = HttpEffectGuard(READ)
    guard.check("GET", REAL_CAMPAIGN)
    assert guard.allowed == [("GET", REAL_CAMPAIGN)]


@pytest.mark.parametrize("endpoint", ["validate", "generate"])
def test_effect_free_generator_posts_allowed_with_their_own_opt_in(endpoint):
    guard = HttpEffectGuard(READ, allow_generator_posts=True)
    guard.check("POST", f"{GENERATOR}/api2/generators/{endpoint}")


def test_effect_free_allowlist_is_exact():
    """A POST that merely looks like the allowlisted ones is still a write."""
    guard = HttpEffectGuard(READ, allow_generator_posts=True)
    with pytest.raises(LiveGuardViolation):
        guard.check("POST", f"{GENERATOR}/api2/generators/generate/extra")


def test_write_phase_allows_write_into_sacrificial_campaign():
    guard = HttpEffectGuard(WRITE, is_sacrificial_target=sacrificial_only)
    guard.check("PATCH", f"{SACRIFICIAL}/logs")
    guard.check("GET", REAL_CAMPAIGN)


def test_delete_phase_allows_ledger_id():
    guard = HttpEffectGuard(DELETE, is_ledger_id=ledger_has)
    guard.check("DELETE", f"{LOGGER}/logs/cccccccccccccccccccccccccccccccc")


# --- installation: the guard must actually sit in the transport --------------


def test_install_intercepts_a_real_session():
    session = requests.Session()
    HttpEffectGuard(READ).install(session)

    with requests_mock.Mocker() as m:
        allowed = m.get(REAL_CAMPAIGN, json={"data": {}})
        m.delete(REAL_CAMPAIGN, status_code=204)

        assert session.get(REAL_CAMPAIGN).status_code == 200
        # The permitted request must go through the *mock*, not the network.
        # An earlier install() captured the bound send at install time, which
        # bypassed requests_mock and reached the real server.
        assert allowed.call_count == 1

        with pytest.raises(LiveGuardViolation):
            session.delete(REAL_CAMPAIGN)


def test_install_blocks_before_the_request_is_sent():
    """The refused request must not reach the transport at all."""
    session = requests.Session()
    HttpEffectGuard(READ).install(session)

    with requests_mock.Mocker() as m:
        matcher = m.delete(REAL_CAMPAIGN, status_code=204)
        with pytest.raises(LiveGuardViolation):
            session.delete(REAL_CAMPAIGN)
        assert matcher.call_count == 0


# --- Phase 0.1: every live request must carry a timeout ----------------------


def test_guard_forces_a_timeout_on_requests_that_lack_one():
    """api.py sets no timeout and hides its Session, so the transport imposes one."""
    session = requests.Session()
    HttpEffectGuard(READ).install(session)
    seen = {}

    with requests_mock.Mocker() as m:
        m.get(REAL_CAMPAIGN, json={"data": {}})
        original = requests.Session.send

        def record(self, request, **kwargs):
            seen.update(kwargs)
            return original(self, request, **kwargs)

        requests.Session.send = record
        try:
            session.get(REAL_CAMPAIGN)
        finally:
            requests.Session.send = original

    assert seen["timeout"] == DEFAULT_TIMEOUT


def test_guard_does_not_override_an_explicit_timeout():
    session = requests.Session()
    HttpEffectGuard(READ).install(session)
    seen = {}

    with requests_mock.Mocker() as m:
        m.get(REAL_CAMPAIGN, json={"data": {}})
        original = requests.Session.send

        def record(self, request, **kwargs):
            seen.update(kwargs)
            return original(self, request, **kwargs)

        requests.Session.send = record
        try:
            session.get(REAL_CAMPAIGN, timeout=1)
        finally:
            requests.Session.send = original

    assert seen["timeout"] == 1
