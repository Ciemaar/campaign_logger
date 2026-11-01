---
conventions-version: 1
conventions-required: 1
---

# Local Conventions

This file states the values this repository's workflow currently repeats across its templates and commands: the check commands, the dispatch invocation, the sensitive-path list, and how repository identity reaches a prompt.

## 1. The check commands

What this repository runs to verify a unit.

- check: `tox -e check` — builds sdist/wheel, `twine check`, `check-manifest`, `ruff check .`, `ruff format --check .`, `pyright .`, `mdformat --check --wrap 80` and `rstfmt --check` on the listed docs (source: `tox.ini` `[testenv:check]`; CI matrix entry `check`)
- test: `tox -e py314-cover` — `pytest -vv --cov=campaign_logger --cov-fail-under=95` (source: `tox.ini`; CI runs it on ubuntu/windows/macos, plus `py315-cover` and `py314-nocov`/`py315-nocov`)
- docs: `tox -e docs` — Sphinx doctest and html build (source: `tox.ini`; CI matrix entry `docs`)
- bootstrap drift: `tox -e bootstrap`, then `git diff --exit-code` — generated `tox.ini` and `.github/workflows/github-actions.yml` must match `ci/templates/` (source: CI job `bootstrap drift`; `AGENTS.md` Workflow)
- action versions: `python ci/check_action_versions.py <base-sha> <head-sha>` — refuses pinned-action downgrades (source: CI job `action versions`, pull requests only)
- audit: `uv audit` — dependency vulnerability audit (source: `.github/workflows/audit.yml`)
- pre-commit: `pre-commit run --all-files` — whitespace, ruff/ruff-format, mdformat (gfm), rstfmt (source: `.pre-commit-config.yaml`)

## 2. The dispatch invocation

How a unit prompt reaches an implementing agent.

None. The artifact discipline (plan, prompt, report) works without any delegation. `AGENTS.md` names Jules as an expected implementer, but the repository does not document how a task is sent to it; delegation is an optional layer, not a requirement.

## 3. The sensitive-path list

The paths whose modification escalates to a human regardless of test results.

Credential-handling code:

- `src/campaign_logger/api.py` — `LoggerClient` sends `api-client`/`api-secret` headers and `GeneratorClient` a Bearer token; the session's `rebuild_auth` override is what stops those custom headers following a cross-host redirect
- `src/campaign_logger/cli.py` — `load_config()` copies `token`/`client_id`/`client_secret` from `~/.campaign_logger.json` into the environment, and `--token`/`--client-secret` accept secrets as options
- `src/campaign_logger/mcp_server.py` — reads `CL_LOGGER_CLIENT_ID`, `CL_LOGGER_CLIENT_SECRET` and `CL_GENERATOR_TOKEN` from the environment
- `.env.example` — the only tracked `.env*`; must never gain real values
- `tests/live_guard.py`, `tests/conftest.py`, `tests/test_live_flags_never_in_ci.py`, `tests/test_redirect_auth.py` — the guard that confines live tests to the sacrificial campaign and keeps live flags out of CI, and the test that pins the redirect credential stripping

CI configuration:

- `.github/workflows/` — `github-actions.yml` (generated) and `audit.yml` (hand-written)
- `ci/templates/`, `ci/bootstrap.py` — source of the generated CI and `tox.ini`
- `ci/check_action_versions.py` — action-pinning gate
- `tox.ini` — generated; the check commands live here
- `.pre-commit-config.yaml`
- `.codacy.yml`, `.github/dependabot.yml`

Dependency manifests:

- `pyproject.toml` — package configuration and dependencies
- `setup.cfg` — the CI `[matrix]`
- `uv.lock`
- `ci/requirements.txt`, `docs/requirements.txt`

The agents' own instruction files:

- `AGENTS.md`
- `.github/copilot-instructions.md`
- `SESSION_INSTRUCTIONS.md`
- `.claude/`

## 4. How repository identity reaches a prompt

There are no prompt templates or generation scripts yet, so identity is not injected anywhere. The only sources are the git remote (`https://github.com/Ciemaar/campaign_logger.git`) and `[project.urls]` in `pyproject.toml`. Until a template injects it, prompts state `Ciemaar/campaign_logger` explicitly.

## 5. Templates to copy

- `templates/plans/TEMPLATE.md`    -> `plans/TEMPLATE.md`
- `templates/prompts/TEMPLATE.md`  -> `prompts/TEMPLATE.md`
- `templates/reports/TEMPLATE.md`  -> `reports/TEMPLATE.md`
- `templates/plans/README.md`      -> `plans/README.md`
- `templates/prompts/README.md`    -> `prompts/README.md`
- `templates/reports/README.md`    -> `reports/README.md`

## 6. Runtime files ignore

- `.dispatch-state.json`
- `.claude/.watch-heartbeat`
- `.claude/.watch-status.json`
- `.claude/.open-pr-cache`
- `.claude/.watch-polls-cache`
