---
id: 36
issues: [36, 37, 38]
title: Close out the static-analysis triage debt (B701, Codacy PR #21, alert snapshot)
status: draft
created: 2026-11-05
updated: 2026-11-05
units:
  - name: bootstrap-selective-autoescape
    assignee: jules
    prompt: /prompts/36-01-bootstrap-selective-autoescape.md
    report:
    pr:
    status: pending
    depends_on: []
  - name: codacy-pr21-findings
    assignee: claude
    prompt: null
    report:
    pr:
    status: blocked
    depends_on: []
  - name: alert-snapshot-decision
    assignee: claude
    prompt: null
    report:
    pr:
    status: blocked
    depends_on: []
---

# 36 — Close out the static-analysis triage debt

## Intent

Three issues from the 2026-09 review are about what the scanners said and
whether anyone read it. Each is mostly resolved in code already; what remains is
a small guard, and two decisions that only the owner can take. This plan
implements all three:

- **#36** — the Jinja2 environment in `ci/bootstrap.py` was built without
  `autoescape` (Bandit B701).
- **#37** — two `high` and one `medium` Security finding on PR #21 were never
  enumerated, so the repo records no triage of them.
- **#38** — 1,288 open code-scanning alerts, which #38's own later comment shows
  are a frozen snapshot no workflow refreshes.

Merely referenced: #69 and #35 (closed, the Codacy configuration work), #96.

## Current state

Checked against `upstream/main` (6ca230e) on 2026-11-05.

- **#36 is fixed in code.** PR #26 merged: `ci/bootstrap.py` now passes
  `autoescape=True` with a comment. The generated `tox.ini` and
  `.github/workflows/github-actions.yml` contain no HTML entities
  (`grep -c '&amp;\|&#' ` returns 0 for both). The issue's warning still stands
  as a latent hazard: `autoescape=True` escapes `&`, `<`, `>` and quotes in
  every value, and the `bootstrap drift` job compares committed output with
  regenerated output, so a corrupted render would be committed and agreed with
  rather than flagged. Alert #553 remains open in the frozen store.
- **#37's second criterion is done.** `AGENTS.md` Workflow already states that
  "Codacy is advisory" does not cover Security findings of `high` or above. The
  first criterion — enumerating the three findings — needs someone logged in to
  `app.codacy.com`; nothing in the repo or in the issue comments holds them.
- **#38 has changed meaning.** The comment thread shows the newest alert is from
  2026-08-29, no workflow uploads SARIF, and the live PR check now passes. The
  remaining configuration item is `D213`, which conflicts with
  `convention = "google"` and can only be switched off on the Codacy Code
  patterns page. `.codacy.yml` already excludes `tests/`, `ci/` and
  `docs/conf.py` per engine (PR #29 itself was closed unmerged).

## Approach

One code unit and two owner-gated units.

- **01 bootstrap-selective-autoescape** is the only dispatchable unit. It makes
  the latent hazard checkable: use `select_autoescape` so non-HTML templates are
  never escaped, and add a test that rendering the committed templates produces
  no HTML entities. It touches `ci/`, which is sensitive, so it escalates to a
  human regardless.
- **02 codacy-pr21-findings** is `blocked` on the owner pasting the three
  findings from the Codacy PR view (or stating that they have aged out). Once
  that exists, the unit records each as fixed or dismissed with a reason in the
  issue. It is `claude` because it is a conversation, not a diff.
- **03 alert-snapshot-decision** is `blocked` on a choice: dismiss the snapshot
  wholesale, or re-enable a SARIF upload. #38 says this needs a workflow and a
  token, so it is not a cleanup. It is `claude` for the same reason.

All three are independent. 02 and 03 are expected to produce documentation and
issue comments rather than code, and dismissing alerts in GitHub is an
outward-facing action that Claude takes only on the owner's say-so.

## Units

### 01 — bootstrap-selective-autoescape

- **Scope:** `ci/bootstrap.py` (the `jinja2.Environment` construction only),
  `tests/test_bootstrap_rendering.py` (new).
- **Out of scope:** `ci/templates/`, the generated `tox.ini` and workflow, the
  matrix in `setup.cfg`, any action version.
- **Acceptance criteria:** `python ci/bootstrap.py` followed by
  `git diff --exit-code` shows no change to the generated files; the new test
  fails if the environment escapes a value containing `&&` or a quote and passes
  today; `tox -e check` and `tox -e py314-cover` pass. See prompt.
- **Depends on:** none

### 02 — codacy-pr21-findings

- **Scope:** an issue comment on #37 and, if the owner agrees,
  `docs/codacy-configuration.md`. To be fixed when the prompt is written.
- **Out of scope:** to be fixed with the prompt.
- **Acceptance criteria:** each of the three findings is named in #37 and marked
  fixed or dismissed with a reason, or #37 records that they are no longer
  retrievable. Specified once the owner supplies them.
- **Depends on:** none

### 03 — alert-snapshot-decision

- **Scope:** `docs/codacy-configuration.md`, issue #38 (retitle). To be fixed
  when the prompt is written.
- **Out of scope:** to be fixed with the prompt.
- **Acceptance criteria:** the chosen option is recorded in the docs and on #38,
  and the open alert count matches the choice. Specified once the owner decides.
- **Depends on:** none

## Sensitive paths

Any diff touching these escalates to a human regardless of test results:

- `ci/bootstrap.py`, `ci/templates/` — source of the generated CI and `tox.ini`
- `.github/workflows/`, `tox.ini` — generated; never edited by hand
- `.codacy.yml`, `.github/dependabot.yml`, `.pre-commit-config.yaml`
- `AGENTS.md`, `.claude/` — agent instruction files; the Codacy wording there is
  already correct and no unit here should touch it
- `pyproject.toml`, `setup.cfg`, `uv.lock`

Unit 01 touches `ci/bootstrap.py` and will always be escalated; that is
expected.

## Risks and unknowns

- **#37 may be unanswerable.** If Codacy has aged out the PR #21 view, the
  honest outcome is a recorded "not retrievable", and #37 closes on that. Bandit
  reporting nothing on current `src/` does not show the findings were fixed;
  nothing establishes Bandit produced them.
- **Which scanner reports the alerts.** Whether `Pylint`, `Prospector` or the
  `E1136` rule are still enabled in Codacy cannot be read from the repository.
- **Alert #553** stays open until someone dismisses it or the snapshot decision
  in unit 03 covers it.
- **`D213` conflict** needs a dashboard change that no commit can make.
- **Dispatch target.** Jules becomes read-only on 2026-11-11 (#155); unit 01's
  `assignee` needs revisiting if no replacement is chosen by approval.

## Not doing

- Re-enabling SARIF upload; that is the choice in unit 03, not a default.
- Fixing individual pylint or prospector findings.
- Changing the Codacy dashboard settings from this repository.
- Touching `AGENTS.md`; the Security-finding wording #37 asked for is present.

## Outcome

<!-- Fill in before archiving. Delete this comment. -->

- **Shipped:**
- **Dropped:**
- **Deviations:**
- **Prompt lessons:**
