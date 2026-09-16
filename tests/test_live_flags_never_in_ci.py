"""Section 8 of issue #62: the live flags must never reach automation.

A live run authenticates as the real user against the real server. Nothing that
runs unattended may be able to trigger one, so this is enforced as a test rather
than recorded as an intention -- the check runs on every CI build, including the
build of the pull request that would have introduced the violation.

The three things checked here are the three ways a live run could start without
someone typing the flag: a workflow passing it, a tox environment passing it, or
a live credential sitting in repository secrets.
"""

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOWS = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))
TEMPLATES = sorted((REPO_ROOT / "ci" / "templates" / ".github" / "workflows").glob("*.yml"))

LIVE_FLAGS = (
    "--run-live-read",
    "--run-live-write",
    "--run-live-delete",
    "--run-live-generators",
    "--run-e2e",
)

#: Environment variables that name a live account. A live credential in CI is
#: a standing risk even if no workflow currently passes a flag.
LIVE_CREDENTIAL_NAMES = (
    "CL_LOGGER_CLIENT_ID",
    "CL_LOGGER_CLIENT_SECRET",
    "CL_GENERATOR_TOKEN",
    "CL_LIVE_SACRIFICIAL_CAMPAIGN_ID",
)


def test_workflows_were_actually_found():
    """Guard the guard: a glob that matches nothing would pass every test below."""
    assert WORKFLOWS, "no workflow files found -- this test would silently pass"  # nosec


@pytest.mark.parametrize("workflow", WORKFLOWS + TEMPLATES, ids=lambda p: p.name)
@pytest.mark.parametrize("flag", LIVE_FLAGS)
def test_no_workflow_passes_a_live_flag(workflow, flag):
    """CI must never opt in to a live run.

    Templates are checked too: ``ci/templates`` generates the workflows, so a
    flag added there would reappear on the next bootstrap (see #56).
    """
    assert flag not in workflow.read_text(), f"{workflow.name} passes {flag}; CI must never run live tests"  # nosec


@pytest.mark.parametrize("secret", LIVE_CREDENTIAL_NAMES)
@pytest.mark.parametrize("workflow", WORKFLOWS + TEMPLATES, ids=lambda p: p.name)
def test_no_workflow_references_a_live_credential(workflow, secret):
    assert secret not in workflow.read_text(), f"{workflow.name} references {secret}; live credentials must not exist in CI"  # nosec


@pytest.mark.parametrize("flag", LIVE_FLAGS)
def test_no_tox_environment_passes_a_live_flag(flag):
    """``tox.ini`` runs unattended in CI, so it is part of the same surface."""
    tox_ini = (REPO_ROOT / "tox.ini").read_text()
    for line in tox_ini.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert flag not in stripped, f"tox.ini passes {flag}: {stripped!r}"  # nosec


def test_live_opt_in_is_flags_only_not_environment_variables():
    """G1 is flags-only on purpose, and ``tox.ini`` has ``passenv = *``.

    An environment variable can be exported into a shell and forgotten, and
    ``passenv = *`` would forward it into every tox environment. If the opt-in
    were ever re-plumbed through ``os.environ``, that combination would make a
    live run reachable without anyone typing a flag.
    """
    conftest = (REPO_ROOT / "tests" / "conftest.py").read_text()
    offenders = re.findall(r"os\.environ[^\n]*RUN_LIVE[^\n]*|getenv\([^\n]*RUN_LIVE[^\n]*", conftest)
    assert not offenders, f"live opt-in must not read environment variables: {offenders}"  # nosec

    e2e = (REPO_ROOT / "tests" / "test_e2e.py").read_text()
    assert "RUN_LIVE_E2E" not in e2e, "the RUN_LIVE_E2E escape hatch is back; it bypasses the flag gate"  # nosec
