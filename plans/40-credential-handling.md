---
id: 40
issues: [40, 42, 41]
title: Harden credential handling in the CLI, config file and auth tests
status: draft
created: 2026-11-05
updated: 2026-11-05
units:
  - name: auth-header-tests
    assignee: jules
    prompt: /prompts/40-01-auth-header-tests.md
    report:
    pr:
    status: pending
    depends_on: []
  - name: config-file-permissions
    assignee: jules
    prompt: /prompts/40-02-config-file-permissions.md
    report:
    pr:
    status: pending
    depends_on: []
  - name: config-without-environ
    assignee: jules
    prompt: /prompts/40-03-config-without-environ.md
    report:
    pr:
    status: pending
    depends_on: [02-config-file-permissions]
  - name: secret-flags
    assignee: jules
    prompt: null
    report:
    pr:
    status: blocked
    depends_on: [03-config-without-environ]
---

# 40 — Harden credential handling in the CLI, config file and auth tests

## Intent

Three open issues describe one subject — how this package receives, stores and
sends credentials — and touch the same two files (`cli.py`, `api.py`). This plan
implements all three:

- **#40** — `~/.campaign_logger.json` is read with no permission check, and
  `load_config()` copies its secrets into `os.environ`, where every subprocess
  inherits them and `/proc/<pid>/environ` exposes them.
- **#42** — `--token` and `--client-secret` accept the literal secret on the
  command line, so it lands in shell history and `ps`.
- **#41** — the authentication setup in `api.py` was excluded from the 95%
  coverage gate by `# pragma: no cover`, so a regression in which headers are
  sent would not be caught.

Merely referenced, not implemented: #39 (redirect credential leak, closed;
`tests/test_redirect_auth.py` pins it), #84 (live-test credentials location,
which pulls the opposite way from #42's `.env` comment — see Risks), #91 (CLI
server targeting, which edits the same option declarations).

## Current state

Checked against `upstream/main` (6ca230e) on 2026-11-05; the issues' line numbers
are stale.

- **#41 is half done.** `grep -rn "pragma: no cover" src/` finds only
  `__main__.py`; the four pragmas in `api.py` are gone. What is missing is the
  assertion the issue asked for: no test asserts `Authorization: Bearer <token>`
  (`grep Bearer tests/` is empty), none asserts that no auth header is set when
  credentials are absent, and `tests/test_redirect_auth.py` only covers the
  `api-client`/`api-secret` pair on redirect.
- **#40 stands as written.** `load_config()` in `src/campaign_logger/cli.py`
  opens the file with no mode check and writes `CL_GENERATOR_TOKEN`,
  `CL_LOGGER_CLIENT_ID` and `CL_LOGGER_CLIENT_SECRET` into `os.environ`.
  `create_mcp_server()` in `src/campaign_logger/mcp_server.py` calls
  `load_config()` and then reads those same variables back, so the MCP server
  depends on the round trip. `default_campaign_id` and `default_log_id` also go
  through `os.environ`, and `cli.py` reads them back there; they are not secrets.
- **#42 stands as written.** `generator` declares
  `@click.option("--token", envvar="CL_GENERATOR_TOKEN")` and `logger` declares
  `--client-id` and `--client-secret` likewise. `docs/usage.rst` and `README.md`
  document `--token` as a supported route.
- Existing CLI tests set credentials with `monkeypatch.setenv`, so they keep
  working if the environment fallback is kept.

## Approach

Four units in two independent lanes joined by one file.

- **01 auth-header-tests** lands first and alone: it pins today's behaviour of
  `api.py` before anything moves, and it is a tests-only diff.
- **02 config-file-permissions** and **03 config-without-environ** both edit
  `load_config()`, so 03 depends on 02 rather than racing it. They are separate
  because 02 is a new check and a doc line, while 03 changes how values flow into
  three call sites (the `generator` and `logger` groups and the MCP server).
  Together they would approach the 300-line limit.
- **04 secret-flags** is `blocked` with `prompt: null`: #42 lists three options
  and the one comment on the issue ("use a .env file for this") does not match
  any of them. It also edits the option declarations 03 changes, so it follows
  03 regardless. Its prompt arrives in its own PR once the owner chooses.

01 and 02 can be dispatched in parallel. All units are `jules` by default; none
needs conversation partway through. (Jules' own end of life is tracked in #155;
see Risks.)

Decisions made in this plan so the prompts need not ask:

- A loosely-permissioned config file **warns on stderr and still loads**. It does
  not refuse: refusing would make an existing MCP server fail at startup, and the
  MCP server's stdout is its protocol channel, so the warning must go to stderr.
- The mode check is skipped on Windows, where POSIX mode bits carry no meaning.
- Secrets leave `os.environ`; the non-secret defaults do not change.

## Units

### 01 — auth-header-tests

- **Scope:** `tests/test_auth_headers.py` (new). No change to `src/`.
- **Out of scope:** `api.py`, existing tests, `tests/test_redirect_auth.py`.
- **Acceptance criteria:** the new tests send a real request through
  `requests-mock` and assert on the request actually received: `GeneratorClient`
  sends `Authorization: Bearer <token>`; `LoggerClient` sends `api-client` and
  `api-secret`; with no credentials, or with only one of `client_id` and
  `client_secret`, neither client sends any auth header. `tox -e py314-cover`
  passes; `tox -e check` passes. See prompt.
- **Depends on:** none

### 02 — config-file-permissions

- **Scope:** `src/campaign_logger/cli.py` (`load_config` only),
  `tests/test_config_permissions.py` (new), `docs/usage.rst`,
  `docs/mcp-server.md`.
- **Out of scope:** where `load_config()` puts values (unit 03), any option
  declaration (unit 04), `mcp_server.py`.
- **Acceptance criteria:** a config file readable by group or others produces a
  stderr warning naming the path and `chmod 600`, and the values still load; a
  `0600` file produces no warning; nothing is written to stdout. `tox -e
  py314-cover` and `tox -e check` pass. See prompt.
- **Depends on:** none

### 03 — config-without-environ

- **Scope:** `src/campaign_logger/cli.py`, `src/campaign_logger/mcp_server.py`,
  `tests/test_config_no_environ.py` (new).
- **Out of scope:** the `--token`/`--client-secret` options themselves (unit 04),
  the permission check (unit 02), `CL_DEFAULT_*` handling.
- **Acceptance criteria:** after `load_config()` and after a CLI invocation that
  used config-file credentials, `os.environ` holds none of `CL_GENERATOR_TOKEN`,
  `CL_LOGGER_CLIENT_ID`, `CL_LOGGER_CLIENT_SECRET` unless the test set them; the
  CLI and the MCP server still authenticate from the file; a real environment
  variable still wins over the file. `tox -e py314-cover` and `tox -e check`
  pass. See prompt.
- **Depends on:** 02-config-file-permissions

### 04 — secret-flags

- **Scope:** `src/campaign_logger/cli.py` option declarations, `docs/usage.rst`,
  `README.md`, tests. To be fixed when the prompt is written.
- **Out of scope:** to be fixed with the prompt.
- **Acceptance criteria:** a secret cannot be supplied as a literal command-line
  argument, or doing so warns; the docs name the supported routes. Specified
  once the owner has chosen between the three options in #42.
- **Depends on:** 03-config-without-environ

## Sensitive paths

Any diff touching these escalates to a human regardless of test results:

- `src/campaign_logger/api.py` — header attachment and `rebuild_auth`
- `src/campaign_logger/cli.py` — `load_config()` and the secret options
- `src/campaign_logger/mcp_server.py` — reads the credential variables
- `tests/conftest.py`, `tests/live_guard.py`,
  `tests/test_live_flags_never_in_ci.py`, `tests/test_redirect_auth.py`
- `.env.example` — must never gain real values
- `AGENTS.md`, `.github/`, `.claude/` — agent instructions and CI; no unit here
  should touch them
- `pyproject.toml`, `setup.cfg`, `uv.lock` — no unit here should touch them

Every unit in this plan touches credential-handling code or its tests; that is
the point of the plan, not an anomaly.

## Risks and unknowns

- **#42 is undecided.** Its options are drop the flags, accept `@file`, or
  prompt. The comment "use a .env file for this" suggests a fourth route
  (loading a `.env`), which is not in the code today and would add a
  dependency or a parser. Unit 04 stays blocked until the owner answers.
- **#84 pulls the other way.** #84 wants live-test credentials moved out of
  `.env.sandbox` into a `campaign_logger.json`; #42's comment points at `.env`.
  Whatever 04 decides should be consistent with #84, or one of them will undo the
  other.
- **Existing users' scripts.** Unit 04, if it drops the flags, is a breaking
  change; the version and changelog treatment is not decided here.
- **The environment is not the only copy.** Removing secrets from `os.environ`
  stops inheritance by subprocesses, but a user who exports them in their own
  shell has chosen that. The plan does not claim to prevent it.
- **MCP stdout.** A stray `print` in the permission check would corrupt the MCP
  protocol stream; the unit 02 tests assert stdout stays empty, which covers only
  the `load_config()` path.
- **Dispatch target.** Jules becomes read-only on 2026-11-11 (#155). If the
  replacement is not chosen by approval time, these units cannot be dispatched as
  written and the `assignee` values need revisiting.

## Not doing

- Encrypting the config file or integrating an OS keyring.
- Creating `~/.campaign_logger.json` from the CLI. The package never writes it,
  so "created as 0600" in #40 is met by documenting the mode, not by code.
- Any change to redirect handling (#39, done).
- Changing `CL_DEFAULT_CAMPAIGN_ID` / `CL_DEFAULT_LOG_ID` handling.
- Per-campaign credentials or multiple profiles.

## Outcome

<!-- Fill in before archiving. Delete this comment. -->

- **Shipped:**
- **Dropped:**
- **Deviations:**
- **Prompt lessons:**
