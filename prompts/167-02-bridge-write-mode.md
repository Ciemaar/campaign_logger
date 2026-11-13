---
plan: 167
unit: 02
name: bridge-write-mode
repo: Ciemaar/campaign_logger
pr:
iteration: 1
---

# 167-02 bridge-write-mode — `bridge start|stop|status --write` for a separate read-write socket

Add an opt-in read-write mode to the `bridge` group from unit 01. **Read-only
remains the default**: without `--write` every command behaves exactly as it
did. Read [issue #167](https://github.com/Ciemaar/campaign_logger/issues/167)
requirement 4 and the plan's *Approach*. If unit 01 has not merged, stop and say
so in the PR description.

# Scope

**Modify only these files:**

- `src/campaign_logger/bridge.py`
- `src/campaign_logger/cli.py` (the `--write` option on the three `bridge`
  commands; nothing else)
- `tests/test_bridge.py` (add tests; leave unit 01's tests unchanged)

**Also in scope, always:** `reports/167-02-bridge-write-mode.md`, from
`reports/TEMPLATE.md`, Part 1 only, before you open the PR.

**Do not modify:**

- existing tests
- `src/campaign_logger/mcp_server.py`, `src/campaign_logger/api.py`
- `pyproject.toml`, `uv.lock`, `setup.cfg`, `tox.ini`, `ci/`, `.github/`,
  `AGENTS.md`, `.claude/`
- docs (unit 03), the sandbox tooling or its allow rules
- any plan or prompt file

If the task appears to require a file outside scope, stop and say so in the PR
description instead of doing it.

# Design (decided; do not choose differently)

- **A second, independent unit pair**, never an edit of the read units:

  ```ini
  # campaign-logger-bridge-write.socket
  [Socket]
  ListenStream=%t/agent-sandbox/mcp/campaign-logger-write.sock
  SocketMode=0600
  DirectoryMode=0700
  Accept=yes

  # campaign-logger-bridge-write@.service
  [Service]
  ExecStart=<absolute path to campaign-logger> mcp --write
  StandardInput=socket
  StandardOutput=socket
  ```

  Use the same executable-path resolution as unit 01.

- **`--write` on `start`, `stop` and `status`** selects the write pair only. The
  read pair is never touched by a `--write` command, and a command without
  `--write` never touches the write pair. `bridge status` with no flag reports
  **both** sockets, labelled, so an open write socket is never hidden.

- **`start --write` says what it does before it does it**: it names the socket,
  and states that a connected agent can create, update and delete campaign data
  with the owner's credentials. It does not ask interactively (a supervisor may
  call it); the printed line is the disclosure.

- **No default and no upgrade path.** Do not add a config option, environment
  variable or flag that makes the read socket serve write tools, or that starts
  the write socket from `bridge start` alone.

- Reuse unit 01's rendering and `systemctl` helpers, parameterised by mode; do
  not copy-paste them. If that needs a refactor of unit 01's code, keep the read
  units' rendered text byte-identical.

# Conventions

**Read `AGENTS.md` first.** Line length 140, ruff and pyright, Python 3.14.
Follow unit 01's code and tests for structure; mock `subprocess.run`; use
`click.testing.CliRunner`.

# Acceptance criteria

- [ ] `tox -e check` passes
- [ ] `tox -e py314-cover` passes, including the coverage floor
- [ ] a test asserts the read units rendered after this change are
  byte-identical to unit 01's expected text
- [ ] a test asserts the write socket unit has the write socket path,
  `SocketMode=0600`, `DirectoryMode=0700`, `Accept=yes`, and the write service
  ends `mcp --write`
- [ ] a test asserts `bridge start` without `--write` makes no call naming a
  write unit, and `start --write` / `stop --write` make no call naming a read
  unit
- [ ] a test asserts `start --write` prints the socket path and that agents can
  change data, before the first `systemctl` call
- [ ] a test asserts `bridge status` reports both sockets
- [ ] a test with the in-test accept loop from unit 01, started with
  `mcp --write`, shows a write tool in the tool list and a write call succeeding
  against a stubbed API, while the read stand-in's tool list still has no write
  tool
- [ ] the report contains the verbatim output of every check above, as text

# Anti-goals

No new dependencies, no change to `mcp_server.py`, no autostart, no network
listener, no weakening of existing tests. Do not claim the units load under a
real systemd: say in the PR description that a human must run
`bridge start --write` once on a real user manager.

# Before you finish

Run the checks, write the report, rerun `tox -e check` so the report is
formatted.

# Test integrity

Do not modify or delete existing tests. New tests only.

# Answering questions

Put questions in the PR description.
