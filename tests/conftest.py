"""Pytest configuration and the G1 live-phase opt-in interlock.

Live tests talk to a real Campaign Logger account holding years of real play
data. There is no test server and no test account, so the opt-in mechanism is a
safety guard, not a convenience: see issue #62.

Three escalating phases plus one orthogonal capability, each gated by its
**own** flag. None implies another -- ``--run-live-write`` does not enable
reads, and neither enables deletes. A test marked for a phase is skipped unless
that exact flag is passed.

``--run-live-generators`` covers the generator ``validate`` and ``generate``
POSTs. They create nothing, but they are still live POSTs against a real
service, so they get their own opt-in rather than riding along with the read
phase.

Flags only, never environment variables. An environment variable can be exported
into a shell and forgotten, or ride through a ``passenv = *`` in tox; a
command-line flag has to be typed for the run it applies to.
"""

import os

import pytest

#: Marker name -> flag that enables it. Deliberately not a hierarchy.
LIVE_PHASES = {
    "live_read": "--run-live-read",
    "live_write": "--run-live-write",
    "live_delete": "--run-live-delete",
    "live_generators": "--run-live-generators",
}


def pytest_addoption(parser):
    """Register the live-phase opt-in flags.

    ``--run-e2e`` is kept as a backwards-compatible alias for ``--run-live-read``
    only, so tests that exist today cannot silently gain write or delete power.
    """
    parser.addoption(
        "--run-live-read",
        action="store_true",
        default=False,
        help="run live read-only tests against the real server (phase 1)",
    )
    parser.addoption(
        "--run-live-write",
        action="store_true",
        default=False,
        help="run live write tests inside the sacrificial campaign (phase 2)",
    )
    parser.addoption(
        "--run-live-delete",
        action="store_true",
        default=False,
        help="run live delete tests (phase 3) -- see issue #62 section 7 before using this",
    )
    parser.addoption(
        "--run-live-generators",
        action="store_true",
        default=False,
        help="run live generator validate/generate POSTs (effect-free, but still live)",
    )
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="deprecated alias for --run-live-read",
    )


def pytest_configure(config):
    """Register the live-phase markers so pytest does not warn about them."""
    config.addinivalue_line("markers", "e2e: deprecated alias for live_read")
    config.addinivalue_line("markers", "live_read: live read-only test (needs --run-live-read)")
    config.addinivalue_line("markers", "live_write: live write test (needs --run-live-write)")
    config.addinivalue_line("markers", "live_delete: live delete test (needs --run-live-delete)")
    config.addinivalue_line("markers", "live_generators: live generator POST test (needs --run-live-generators)")


def live_phase_enabled(config, marker):
    """Return whether the flag for ``marker`` was passed on this run.

    ``e2e`` and ``live_read`` are both satisfied by ``--run-live-read``; ``e2e``
    is additionally satisfied by the deprecated ``--run-e2e``.
    """
    if marker == "e2e":
        return bool(config.getoption("--run-e2e") or config.getoption("--run-live-read"))
    flag = LIVE_PHASES.get(marker)
    if flag is None:
        return True
    enabled = bool(config.getoption(flag))
    if marker == "live_read":
        enabled = enabled or bool(config.getoption("--run-e2e"))
    return enabled


def pytest_collection_modifyitems(config, items):
    """Skip each live-phase test unless its own flag was given.

    A test carrying several live markers needs every one of their flags: the
    strictest reading, so a mixed-phase test cannot run half-authorised.
    """
    gated = ["e2e", *LIVE_PHASES]
    for item in items:
        for marker in gated:
            if marker in item.keywords and not live_phase_enabled(config, marker):
                item.add_marker(pytest.mark.skip(reason=f"need {LIVE_PHASES.get(marker, '--run-live-read')} option to run"))
                break


# --- Phase 1 live read-only fixtures (issue #62) -----------------------------


@pytest.fixture(scope="session")
def sandbox_config():
    """The verified sacrificial-campaign config, or skip if not set up.

    Reads never need the sandbox, but the read tests assert against it to prove
    they are talking to the account we think they are.
    """
    from live_sandbox import SandboxConfigError
    from live_sandbox import load_sandbox_config

    try:
        return load_sandbox_config(os.environ)
    except SandboxConfigError as exc:
        pytest.skip(f"live sandbox not configured: {exc}")


@pytest.fixture
def live_read_client():
    """A LoggerClient in READ phase, built from the environment.

    Skips cleanly when the credentials are absent, so the suite is safe to run
    without them. The guard forces a timeout and refuses anything but GET (plus
    the effect-free generator POSTs, which are not enabled here).
    """
    client_id = os.environ.get("CL_LOGGER_CLIENT_ID")
    client_secret = os.environ.get("CL_LOGGER_CLIENT_SECRET")
    if not client_id or not client_secret:
        pytest.skip("CL_LOGGER_CLIENT_ID / CL_LOGGER_CLIENT_SECRET not set")

    from live_guard import READ
    from live_guard import HttpEffectGuard

    from campaign_logger.api import LoggerClient

    client = LoggerClient(
        base_url=os.environ.get("CL_LOGGER_URL", "https://logger-staging.campaign-logger.com"),
        client_id=client_id,
        client_secret=client_secret,
    )
    HttpEffectGuard(READ).install(client.session)
    return client
