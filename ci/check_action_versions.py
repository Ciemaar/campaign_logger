#!/usr/bin/env python
"""Fail when merging a branch would downgrade a pinned GitHub Action (issue #61).

``.github/workflows/audit.yml`` was silently reverted by two separate pull
requests -- ``checkout@v7`` back to ``v4``, ``setup-uv@v10.0.1`` back to
``v5.1.0`` -- neither of which was about CI. Both rode along in a large diff, and
the second survived a review that checked the PR's stated changes.

Why this compares the *merge result* rather than the branch
----------------------------------------------------------
``git diff base..head`` answers "how do these trees differ", not "what would
merging apply". A branch merely behind ``main`` reports every later commit as a
deletion -- measured at 183 spurious deletions on a branch six commits behind.
``git merge-tree --write-tree`` computes the merge without a working tree, so
diffing its result against the base shows what the merge would really do.

Why action versions rather than deleted lines
---------------------------------------------
"Lines deleted from a workflow" is too blunt: a pull request that legitimately
rewrites a workflow deletes lines, and issue #61 measured one branch at 44
deletions that were all its own edits. Comparing the *set of pinned action
versions* is mechanical and has no such ambiguity -- a version going backwards is
never intentional-but-unexplained, and it is exactly what happened twice.

Requires git 2.38+ for ``merge-tree --write-tree``.
"""

import re
import subprocess  # nosec B404 - git plumbing, fixed argument lists, no shell
import sys

#: ``uses: owner/repo@ref`` in a workflow, capturing the action and its ref.
USES = re.compile(r"^\s*-?\s*uses:\s*(?P<action>[^@\s]+)@(?P<ref>\S+)", re.M)

#: A ref pinned to a commit rather than a tag. Not comparable as a version.
SHA_REF = re.compile(r"^[0-9a-f]{40}$")

WORKFLOW_DIR = ".github/workflows"


def git(*args):
    """Run a git command and return its stdout, raising on failure."""
    return subprocess.run(  # nosec B603 B607 - fixed argv, no shell, args are git refs
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def merge_tree(base, head):
    """The tree a merge of ``head`` into ``base`` would produce, or None on conflict.

    ``merge-tree`` exits non-zero and prints the conflicted paths instead of a tree
    when the merge does not apply cleanly. That is not a pass: it means the question
    could not be answered, so the caller is told rather than reassured.
    """
    result = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["git", "merge-tree", "--write-tree", base, head], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip().splitlines()[0]


def pinned_versions(tree):
    """``{"path::action": ref}`` for every action used by any workflow in ``tree``.

    Keyed per file, not per action. Two workflows may pin different versions of the
    same action -- and they did here, which is the whole problem -- so a single
    action-keyed mapping would let a downgrade in one file be masked by the other.
    """
    listing = git("ls-tree", "-r", "--name-only", tree, "--", WORKFLOW_DIR)
    found = {}
    for path in listing.splitlines():
        if not path.endswith((".yml", ".yaml")):
            continue
        for match in USES.finditer(git("show", f"{tree}:{path}")):
            found[f"{path}::{match.group('action')}"] = match.group("ref")
    return found


def version_tuple(ref):
    """``v10.0.1`` -> ``(10, 0, 1)``, or None when the ref is not a plain version."""
    cleaned = ref.lstrip("vV")
    if not cleaned or not re.fullmatch(r"\d+(\.\d+)*", cleaned):
        return None
    return tuple(int(part) for part in cleaned.split("."))


def downgrades(before, after):
    """Actions whose version went backwards, and actions that disappeared."""
    lowered, removed = [], []
    for action, old_ref in before.items():
        if action not in after:
            removed.append((action, old_ref))
            continue
        new_ref = after[action]
        if new_ref == old_ref or SHA_REF.match(new_ref) or SHA_REF.match(old_ref):
            continue
        old_version, new_version = version_tuple(old_ref), version_tuple(new_ref)
        if old_version and new_version and new_version < old_version:
            lowered.append((action, old_ref, new_ref))
    return lowered, removed


def modified_workflows(base, head):
    """Workflow files ``head`` changed since it diverged from ``base``.

    A branch that never touched a workflow cannot revert it: git keeps the base's
    version, and the branch merely being stale is not a finding. Restricting to the
    files the branch actually edited is what keeps this from firing on every branch
    that is behind -- the same trap that makes a two-dot diff useless here.
    """
    merge_base = git("merge-base", base, head).strip()
    changed = git("diff", "--name-only", f"{merge_base}..{head}", "--", WORKFLOW_DIR)
    return {path for path in changed.splitlines() if path.endswith((".yml", ".yaml"))}


def report(lowered, removed):
    """Print findings as GitHub annotations."""
    for key, old_ref, new_ref in lowered:
        path, action = key.split("::", 1)
        print(f"::error file={path}::Merging this branch would downgrade {action} from {old_ref} to {new_ref} in {path}.")
    for key, old_ref in removed:
        path, action = key.split("::", 1)
        print(f"::warning file={path}::Merging this branch would stop using {action} (was {old_ref}) in {path}.")


def main(argv):
    """Compare ``base`` and ``head``; return a process exit code."""
    if len(argv) != 2:
        print("usage: check_action_versions.py <base-sha> <head-sha>", file=sys.stderr)
        return 2
    base, head = argv

    before = pinned_versions(base)
    tree = merge_tree(base, head)

    if tree is not None:
        # The authoritative comparison: what the merge would actually produce.
        lowered, removed = downgrades(before, pinned_versions(tree))
    else:
        # The merge conflicts, which is precisely where someone resolves it by hand
        # and may take the branch's side. Going quiet here would be worst: the
        # question is unanswered, not answered favourably. So compare the branch
        # directly, limited to workflows the branch actually edited.
        touched = modified_workflows(base, head)
        if not touched:
            print("Merge conflicts, but this branch edits no workflow. Nothing to check.")
            return 0
        print(f"::warning::Merge conflicts; comparing the branch directly for {', '.join(sorted(touched))}.")
        after = pinned_versions(head)
        relevant = {key: ref for key, ref in before.items() if key.split("::", 1)[0] in touched}
        lowered, removed = downgrades(relevant, after)

    report(lowered, removed)

    if lowered:
        print(
            "\nThis is what issue #61 is about: a branch created before the upgrade "
            "landed carries the older pin, and editing the same workflow reinstates it. "
            "Rebase onto the base branch and push again.",
            file=sys.stderr,
        )
        return 1

    print(f"No action downgrades. Checked {len(before)} pinned actions.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
