---
plan:
unit:
name: onboard-agent-workflow
prompt:
iteration: 1
author: claude
reviewer: Andy Fundinger
session: https://claude.ai/code/session_01EQrwqUs8NnTHyKsejrqqa2
pr:
verdict:
opened: 2026-11-01
reviewed:
partial:
---

# Report — onboard-agent-workflow

- **Diff:** see the PR (17 files: 9 edited, 8 added)
- **Prompt:** none — direct session with the owner via the
  `agent-repo-workflow:onboard-workflow` skill
- **Implemented by:** claude — **Verified by:** human (PR review)

______________________________________________________________________

## Part 1 — Implementation record

### What changed, and why

Adopts the agent-repo-workflow: `.claude/reference/local-conventions.md` records
the real check commands, the sensitive paths, the Jules dispatch invocation
(`agent-repo-tools prompt-repos`) and how repo identity reaches a prompt; the six plan/prompt/report templates are copied
verbatim from the plugin; runtime state files are gitignored; `AGENTS.md` gains
a Reporting section requiring a committed report before a PR opens. While
reading `AGENTS.md` for that, it was found to contradict practice, and the owner
ruled that practice wins: the code already declares Python 3.14
(`requires-python`, ruff, pyright, CI), so the docs that still said 3.11–3.14 or
`py312-cover` are brought into line, `audit.yml` moves from 3.13 to 3.14, and
build docs that pointed at a `setup.py` that no longer exists now point at
`pyproject.toml`. Moving to 3.15 is deferred to #146.

### Criteria as claimed

<!-- mdformat off -->

| #   | criterion                                         | command run                                             | claimed result                    |
| --- | ------------------------------------------------- | ------------------------------------------------------- | --------------------------------- |
| 1   | No stale 3.11–3.13 / `py312` / `setup.py` refs in live docs | `git grep -nE '3\.1[1-3]\|py31[1-3]\|setup\.py'` | only history and two dead `pyproject.toml` entries remain (see Left undone) |
| 2   | Templates byte-identical to the plugin's          | `cmp` per file                                          | all six identical                 |
| 3   | Lint/types/format pass                            | `tox -e check`                                          | OK                                |
| 4   | Tests pass                                        | `tox -e py314-cover`                                    | 482 passed, 12 skipped (live)     |

<!-- mdformat on -->

### Local checks at PR-open

<!-- mdformat off -->

| check      | command              | result                                                           |
| ---------- | -------------------- | ---------------------------------------------------------------- |
| check      | `tox -e check`       | OK — ruff clean, 61 files formatted, pyright 0 errors, mdformat/rstfmt pass, check-manifest match |
| tests      | `tox -e py314-cover` | `482 passed, 12 skipped, 3 warnings in 6.06s`, coverage gate met |
| formatting | `uvx mdformat --check --wrap 80 AGENTS.md` | pass (after one reflow)                       |

<!-- mdformat on -->

The first `tox -e check` passed only because the new files were still
untracked. Once staged, check-manifest failed: `plans/`, `prompts/`, `reports/`
and `.claude/reference/` were missing from the sdist. They are workflow
artifacts, not package content, so they were added to `[tool.check-manifest]
ignore` in `pyproject.toml` beside `AGENTS.md`; `tox -e check` then passed on
the staged tree.

### Deviations from the prompt

The skill's proposal said "`tox -e py312-cover`"-era values were wrong but left
`AGENTS.md` fixes out of scope; the owner widened scope to correct them here.
`tests/test_redirect_auth.py` was added to the sensitive list after reviewing
`api.py`'s redirect credential stripping. `pyproject.toml` (a sensitive
dependency manifest) is touched, but only in `[tool.check-manifest]`.

### Left undone

- Historical records still mention old versions/`setup.py` and were left as
  history: `SESSION_INSTRUCTIONS.md` §6, `docs/tooling_evaluation.md`,
  `docs/requirements.md` row 7.1 (whose status text is itself stale, #48).
- `.pylintrc` comment already says 3.14; untouched.
- `pyproject.toml` still has a ruff per-file-ignore for `setup.py` and a pytest
  `--ignore=setup.py`. Both are harmless leftovers from before the file was
  removed. `tests/test_version_config.py` mentions `setup.py` as history.
- No version bump: `docs/requirements.md` 7.1 asks for one per PR but recent
  merged PRs do not do it.

### Uncertain about

- Dispatch is documented from the plugin's `dispatch` command, but
  `agent-repo-tools` is not installed on the machine this was written on, so the
  invocation was not run with a real prompt (none exists yet). The CLI lives in
  the AgenticRulesAndTools checkout; its `prompt-repos --help`, the `gh` login
  and `jules remote list --session` were confirmed working, and the flags were
  confirmed by that repo's own session.
- Whether `bumpversion patch` is the release step the owner actually uses
  (`PYPI_UPLOAD_INSTRUCTIONS.md` now says so, based on `.bumpversion.cfg`).
- Whether listing whole files (`api.py`, `cli.py`) as sensitive is too coarse;
  the sensitive parts are the auth headers/`rebuild_auth` and `load_config()`.

______________________________________________________________________

## Part 2 — Independent verification

Implemented by Claude; there is no independent agent reviewer. Verification is
the owner's review in the PR comments.
