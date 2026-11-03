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

```bash
agent-repo-tools prompt-repos Ciemaar/campaign_logger \
    --prompt-file prompts/<N>-NN-<slug>.md
```

This repository adopts the plugin's Jules dispatch. Always pass the target repository explicitly (the prompt's `repo:` value) and pass the prompt file, not inline text, so what is dispatched is byte-identical to what is committed. Use `--dry-run` first to see the target list without sending anything. Jules opens its work as a draft pull request. `prompt-repos` records the session in `.dispatch-state.json` (gitignored); read it back with `agent-repo-tools sessions list`, and never commit a session id.

Requirements on the machine that dispatches:

- The `agent-repo-tools` CLI. Plugin `agent-repo-workflow` 1.1.1 or newer puts it on the Bash tool's `PATH` through its own launcher (`bin/agent-repo-tools`, which runs the pinned release via `uvx`). That needs `uv` and git credentials for the private `Ciemaar/AgenticRulesAndTools` repository (`gh auth setup-git`). Check with `agent-repo-tools --version`. A session that started before the plugin was upgraded does not have it on `PATH`; restart the session. Plugin 1.0.0 shipped no CLI at all.
- The `jules` CLI, logged in (`jules remote list --session` should work).
- `GH_TOKEN` in the environment, e.g. `GH_TOKEN=$(gh auth token)` inline; never print it.
- Redirect stdin (`</dev/null`) when running from a non-interactive session, or the CLI can block.
- Never pass `--force`. Without it, dispatch refuses unless the prompt's plan is `approved` on `origin/main` of the target repo, which is the gate we want.
- `.dispatch-state.json` is per working directory. `sessions list` only shows dispatches made from the directory you run it in, so run dispatch from this repository's checkout (a dispatch run from the hub checkout will not appear in this ledger).

Other rules: dispatch consumes Jules quota: stop and ask before opening an eleventh session in one Claude session. Units with `assignee: claude` are worked in-session and are not dispatched.

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

Through the `repo:` frontmatter field of each prompt (`prompts/TEMPLATE.md`), set to `Ciemaar/campaign_logger`. Dispatch passes that value to `agent-repo-tools prompt-repos` as the target repository; nothing is hardcoded in the body of the prompt, and the plugin strips the frontmatter before sending.

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
