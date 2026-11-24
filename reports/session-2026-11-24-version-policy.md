---
plan:
unit:
name: version-policy
prompt:
iteration: 1
author: claude
reviewer: Andy Fundinger
session: https://claude.ai/code/session_01EQrwqWTKhaaQASKkvzhmr5
pr:
verdict:
opened: 2026-11-24
reviewed:
partial:
---

# Report — version-policy

- **Diff:** `.bumpversion.cfg`, `AGENTS.md`, `PYPI_UPLOAD_INSTRUCTIONS.md`,
  `docs/requirements.md`, `tests/test_version_config.py`, this report
- **Prompt:** none. The owner asked in session, 2026-11-24: "Coordinate and
  adopt the hub's version policy" and "bump the version to 0.1.0 when we land
  the usable bridge."
- **Implemented by:** claude — **Verified by:** human (PR review)

______________________________________________________________________

## Part 1 — Implementation record

### What changed, and why

Adopts the hub's release policy (hub plan 618, Ciemaar/AgenticRulesAndTools#618)
for this single package. Implements #182.

- `AGENTS.md`: a "Versions" section. Feature, fix and dependency pull
  requests do not change the version; a release pull request does, using
  `bumpversion minor` or `patch`; the owner tags `vX.Y.Z` on its head commit
  before merging, with a merge commit; agents never run `git tag`.
- `.bumpversion.cfg`: `tag = False` (was `True`). With `True`, a bare
  `bumpversion minor` would create the tag the policy reserves for the owner.
  `tests/test_version_config.py` gains a test that pins it.
- `docs/requirements.md` 7.1 is reworded from "Patch version increases with
  every PR" to the release-pull-request rule and marked **Partial**.
- `PYPI_UPLOAD_INSTRUCTIONS.md`: the upload steps no longer tell the uploader to
  run `bumpversion patch`.

The classification criteria are the hub's, from `plugin-packaging-decisions.md`
§3 (owner's request, 2026-11-24): the version describes what a user must do
(major: change something they wrote; minor: new capability they can ignore;
patch: wording, fixes, accumulates unbumped), an agent classifies a change as it
lands and prepares the release pull request for a minor or major, and a close
call takes the higher level. "Adopter" became "user of the API, CLI and MCP
tools".

Adapted, not copied: the hub has one tag for a CLI and a plugin; this has one
package, so there is no lockstep and no plugin version. The hub's "minor when
the CLI gains commands, patch accumulates with no bump" is kept as is.

The 0.1.0 release itself is not in this pull request. It waits for #174 and is
tracked in #183. The hub-side follow-up, so onboarding documents and enforces a
version policy for every adopter, is Ciemaar/AgenticRulesAndTools#643.

### Local checks at PR-open

Run in a clean worktree on `upstream/main` (`a9611f7`) plus this change:

- `tox -e check`: OK. The first run failed `mdformat --check` on
  `PYPI_UPLOAD_INSTRUCTIONS.md` (my wrapping); reformatted with mdformat and
  re-run: ruff, pyright (0 errors), check-manifest, twine, mdformat and rstfmt
  all pass.
- `tox -e py314-cover`: 483 passed, 12 skipped (live tests). The coverage gate
  is part of that command and passed.
- Not run: CI on other platforms, `bumpversion` itself.

### Deviations from the prompt

There is no prompt. The "usable bridge" in the owner's instruction is read as
#174 (`bridge start|stop|status`), which was run under real systemd on
2026-11-24. If the owner meant all three units of plan 167, #183 and the
`AGENTS.md` sentence naming #174 change.

### Left undone

- A check that fails when a feature pull request changes the version. The
  agreement test catches inconsistent versions, not a premature bump.
- `CHANGELOG.rst` stops at 0.0.0 (2022-02-08). The release pull request adds the
  first real entry; this one does not.
- Whether `bumpversion` (which implementation is installed was not checked)
  honours `tag = False`. It is standard `.bumpversion.cfg` syntax, but no bump
  was run.

### Uncertain about

- Before 1.0, a breaking change is written as a **minor** bump, which departs
  from the hub's "major" wording. §3 has no 0.x rule, so this is my adaptation.
  The owner may prefer the hub's text exactly.
- §3 lets an agent cut the release unsupervised; plan 618 narrowed that to
  "prepare, owner tags". The sentence follows plan 618, as the hub now does.

- Whether the owner wants "agents never run `git tag`" as a hard rule here or
  only for releases. It is written as a hard rule, as in the hub.
- Sensitive paths touched (`.claude/reference/local-conventions.md` §3):
  **`AGENTS.md`**. Escalates to a human regardless of test results.

______________________________________________________________________

## Part 2 — Independent verification

Not written. This unit is `claude`-implemented and cannot be self-reviewed; see
the pull request.
