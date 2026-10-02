"""The action-downgrade guard must catch a real revert topology (#61).

The shape that matters is specific, and it is why a plain ``git diff`` does not
work: the branch is cut **before** an upgrade lands on the base, so the branch's
own history shows no change at all. Comparing the branch to its parent finds
nothing; comparing what the *merge* would produce finds the revert.

Each test builds that topology in a throwaway repository rather than asserting
against this one's history, so it stays true as this repository moves.
"""

import subprocess  # nosec B404 - building fixture repositories with fixed argv
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).parent.parent / "ci" / "check_action_versions.py"

WORKFLOW = ".github/workflows/audit.yml"


def run_git(repo, *args):
    """Run git in ``repo``."""
    subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )


def workflow_text(checkout, setup_uv):
    """A minimal but realistic workflow pinning two actions."""
    return (
        "name: audit\non: [push]\njobs:\n  audit:\n    runs-on: ubuntu-latest\n    steps:\n"
        f"    - uses: actions/checkout@{checkout}\n"
        f"    - uses: astral-sh/setup-uv@{setup_uv}\n"
    )


def write_workflow(repo, checkout, setup_uv):
    """Write the workflow into ``repo``, creating its directory."""
    path = repo / WORKFLOW
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(workflow_text(checkout, setup_uv), encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    """A repository whose ``main`` has upgraded actions after a branch was cut.

    Returns ``(path, base_sha, branch_sha)``. The branch never touches the versions
    -- it simply predates the upgrade, which is the whole point of #61.
    """
    path = tmp_path / "repo"
    path.mkdir()
    run_git(path, "init", "-q", "-b", "main")
    run_git(path, "config", "user.email", "test@example.invalid")
    run_git(path, "config", "user.name", "Test")

    # The commit the branch will be cut from: old pins.
    write_workflow(path, "v4", "v5.1.0")
    run_git(path, "add", "-A")
    run_git(path, "commit", "-qm", "initial")
    fork_point = subprocess.run(  # nosec B603 B607
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True
    ).stdout.strip()

    # main upgrades them (as dependabot did).
    write_workflow(path, "v7", "v10.1.0")
    run_git(path, "add", "-A")
    run_git(path, "commit", "-qm", "chore(deps): bump actions")
    base = subprocess.run(  # nosec B603 B607
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True
    ).stdout.strip()

    # A feature branch cut from before the upgrade, which also edits the workflow
    # for an unrelated reason. That edit is what makes the merge take the branch's
    # whole file -- and with it the old pins. A branch that never touched the
    # workflow merges cleanly and keeps main's upgrade, which is why
    # test_an_unrelated_branch_produces_no_false_positive passes.
    run_git(path, "checkout", "-q", "-b", "feature", fork_point)
    (path / "feature.py").write_text("x = 1\n", encoding="utf-8")
    (path / WORKFLOW).write_text(
        workflow_text("v4", "v5.1.0").replace("    steps:\n", "    steps:\n    - name: a step this branch adds\n      run: echo hi\n"),
        encoding="utf-8",
    )
    run_git(path, "add", "-A")
    run_git(path, "commit", "-qm", "feat: unrelated work, and a workflow tweak")
    branch = subprocess.run(  # nosec B603 B607
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True
    ).stdout.strip()

    return path, base, branch


def check(repo_path, base, head):
    """Run the guard, returning ``(exit_code, combined_output)``."""
    result = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        [sys.executable, str(CHECKER), base, head],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout + result.stderr


def test_a_branch_that_predates_the_upgrade_is_caught(repo):
    """The exact shape that reverted audit.yml twice."""
    path, base, branch = repo

    code, output = check(path, base, branch)

    assert code == 1, output
    assert "downgrade actions/checkout from v7 to v4" in output
    assert "downgrade astral-sh/setup-uv from v10.1.0 to v5.1.0" in output


def test_the_branch_diff_shows_no_version_change(repo):
    """Why the merge result has to be what is measured.

    The branch's own diff shows only the step it added. Relative to where the branch
    was cut, the versions never changed -- so a reviewer reading this pull request's
    diff sees a plausible workflow tweak and no downgrade at all. The downgrade only
    exists relative to the base branch, which is what the guard compares.
    """
    path, _, branch = repo
    diff = subprocess.run(  # nosec B603 B607
        ["git", "diff", f"{branch}^", branch, "--", WORKFLOW],
        cwd=path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    # Only added/removed lines are the review surface; the version lines appear as
    # unchanged context, which is exactly why they read as innocuous.
    changed_lines = [line for line in diff.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))]
    assert any("a step this branch adds" in line for line in changed_lines)
    assert not [line for line in changed_lines if "checkout@" in line or "setup-uv@" in line]


def test_a_rebased_branch_passes(repo):
    """The fix the error message tells you to apply must actually work."""
    path, base, _ = repo
    run_git(path, "checkout", "-q", "feature")
    # The rebase conflicts, because both sides edited the same lines. That is the
    # moment the revert is normally introduced: resolving in the branch's favour
    # reinstates the old pins. Resolved here the way it should be -- keep the
    # upgraded versions, keep the branch's added step.
    subprocess.run(  # nosec B603 B607
        ["git", "rebase", base], cwd=path, capture_output=True, text=True, check=False
    )
    (path / WORKFLOW).write_text(
        workflow_text("v7", "v10.1.0").replace("    steps:\n", "    steps:\n    - name: a step this branch adds\n      run: echo hi\n"),
        encoding="utf-8",
    )
    run_git(path, "add", "-A")
    env_continue = {"GIT_EDITOR": "true"}
    subprocess.run(  # nosec B603 B607
        ["git", "-c", "core.editor=true", "rebase", "--continue"],
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
        env={**__import__("os").environ, **env_continue},
    )
    rebased = subprocess.run(  # nosec B603 B607
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True
    ).stdout.strip()

    code, output = check(path, base, rebased)

    assert code == 0, output
    assert "No action downgrades" in output


def test_a_deliberate_upgrade_passes(repo):
    """Going forwards is not a downgrade -- dependabot must not be blocked."""
    path, base, _ = repo
    run_git(path, "checkout", "-q", "-b", "bump", base)
    write_workflow(path, "v8", "v11.0.0")
    run_git(path, "add", "-A")
    run_git(path, "commit", "-qm", "chore(deps): bump further")
    head = subprocess.run(  # nosec B603 B607
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True
    ).stdout.strip()

    code, output = check(path, base, head)

    assert code == 0, output


def test_an_unrelated_branch_produces_no_false_positive(repo):
    """A branch that is simply behind must not be reported.

    ``git diff base..head`` reports every later commit as a deletion for such a
    branch -- 183 spurious deletions were measured on one. The merge-result
    comparison reports nothing, which is the reason for the whole approach.
    """
    path, base, _ = repo
    run_git(path, "checkout", "-q", "-b", "clean", base)
    (path / "other.py").write_text("y = 2\n", encoding="utf-8")
    run_git(path, "add", "-A")
    run_git(path, "commit", "-qm", "feat: something else")
    head = subprocess.run(  # nosec B603 B607
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True
    ).stdout.strip()

    code, output = check(path, base, head)

    assert code == 0, output


def test_a_removed_action_warns_but_does_not_fail(repo):
    """Dropping an action can be legitimate, so it is surfaced, not blocked."""
    path, base, _ = repo
    run_git(path, "checkout", "-q", "-b", "drop", base)
    (path / WORKFLOW).write_text(
        "name: audit\non: [push]\njobs:\n  audit:\n    runs-on: ubuntu-latest\n    steps:\n    - uses: actions/checkout@v7\n",
        encoding="utf-8",
    )
    run_git(path, "add", "-A")
    run_git(path, "commit", "-qm", "ci: drop setup-uv")
    head = subprocess.run(  # nosec B603 B607
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True
    ).stdout.strip()

    code, output = check(path, base, head)

    assert code == 0, output
    assert "stop using astral-sh/setup-uv" in output


def test_a_sha_pin_is_not_compared(repo):
    """A commit pin has no version ordering, so it must not be guessed at."""
    path, base, _ = repo
    run_git(path, "checkout", "-q", "-b", "sha", base)
    write_workflow(path, "a" * 40, "v10.1.0")
    run_git(path, "add", "-A")
    run_git(path, "commit", "-qm", "ci: pin checkout by sha")
    head = subprocess.run(  # nosec B603 B607
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True
    ).stdout.strip()

    code, output = check(path, base, head)

    assert code == 0, output
    assert "checkout" not in output.replace("No action downgrades", "")
