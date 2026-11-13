---
id: 167
issues: [167]
title: Ship an opt-in MCP bridge for sandboxes, started only on request
status: draft
created: 2026-11-13
updated: 2026-11-13
units:
  - name: bridge-command
    assignee: claude   # Jules is shut down; see Approach. The hub's plan 570 calls this assignee `agent`.
    prompt: /prompts/167-01-bridge-command.md
    report:
    pr:
    status: pending
    depends_on: []
  - name: bridge-docs
    assignee: claude
    prompt: /prompts/167-02-bridge-docs.md
    report:
    pr:
    status: blocked   # waits for 01, so it documents the command as merged
    depends_on: [bridge-command]
---

# 167 — Ship an opt-in MCP bridge for sandboxes, started only on request

## Intent

A sandboxed agent reaches Campaign Logger's read-only MCP server through a unix
socket that a process on the host serves. Today that process is a hand-typed
`socat` command that dies with the shell that started it and is documented only
in the AgenticRulesAndTools hub. The owner wants the bridge to be a feature of
this repository: **present once Campaign Logger is installed, running only when
asked for.** Campaign Logger is a structured database that helps plan
roleplaying games; it does not run a game, and the documentation this plan
produces must not describe it as running one.

**Implemented by this plan:**
[#167](https://github.com/Ciemaar/campaign_logger/issues/167). **Referenced, not
implemented:** [#159](https://github.com/Ciemaar/campaign_logger/issues/159) (an
HTTP transport; the owner has decided the unix-socket bridge is the route for
local MCP servers and that #159 is not planned), hub plan 570
(Ciemaar/AgenticRulesAndTools PR 584, still a draft) and hub issues 570 and 545,
which own the sandbox side and the `agy-rpg` example. Nothing in the sandbox
tooling changes here.

## Current state

- `campaign-logger mcp` (`src/campaign_logger/cli.py`, function `mcp`) runs the
  MCP server over stdio. It is read-only unless `--write` is passed;
  `create_mcp_server(read_only=True)` in `src/campaign_logger/mcp_server.py`
  never registers the write tools.
- `get_tag_types` needs no credentials, so it can be called on a fresh install.
- Nothing in the package opens a socket or touches systemd. The interim bridge
  is the host command in the issue:
  `socat UNIX-LISTEN:"$XDG_RUNTIME_DIR"/agent-sandbox/mcp/campaign-logger.sock,fork,mode=600,unlink-early EXEC:<venv>/bin/campaign-logger mcp`.
- `docs/mcp-server.md` and `docs/mcp_integration.rst` describe the server;
  neither mentions a bridge.
- Tests for the server are in `tests/test_mcp.py` and `tests/test_mcp_tools.py`.

## Approach

**Design (the owner's, from the issue and hub plan 570):** a systemd user
**socket-activated** unit. A `.socket` unit with `Accept=yes` listens at
`$XDG_RUNTIME_DIR/agent-sandbox/mcp/campaign-logger.sock` (directory `0700`,
socket `0600`, so the sandbox side does not change), and a `.service` template
runs `campaign-logger mcp` per connection with stdin and stdout on the socket.
Nothing idles between connections. `campaign-logger bridge start|stop|status`
writes the unit files, runs `systemctl --user enable --now` or `disable --now`,
and reports. Installing the package enables nothing.

**Read-only is structural.** The service line never contains `--write`. There is
no write socket; if the owner wants one later it is a separate change with its
own explicit name.

**Units.** 01 is the command, the unit rendering and the tests, because they are
one reviewable change that cannot be checked apart. 02 is the documentation,
sequenced after 01 so it describes what merged and says what the bridge does
before it acts and how to remove it. 01 is not split further: the module is
small and the tests mostly render text.

**Assignee: why `claude`, and what changed.** Every unit used to be `jules`.
Jules has been read-only since 2026-11-11 and nothing may be dispatched to it.
The hub's replacement (Antigravity, hub plan 433) has no dispatch backend yet.
Per the hub agent (2026-11-13), `claude` is the only assignee value known to
work; `operator` is used in hub plans but its validator is unbuilt, and the hub
plan 570 labels this unit `agent`, meaning the agent in this repository does it
once the new dispatch framework is available here. So both units are `claude`.
If an Antigravity backend arrives before 01 starts, switching the value is a
frontmatter edit and the prompt already reads as a self-contained brief.

**Testing a socket-activated service without systemd.** CI has no user manager.
The tests therefore (a) mock `subprocess.run` for every `systemctl` call, (b)
assert the rendered units, and (c) stand in for systemd with a small in-test
accept loop that serves one subprocess `campaign-logger mcp` per connection on a
socket of mode `0600` in a mode `0700` directory, then connects an MCP client
and calls `get_tag_types`. That proves the requirement's actual claims: a read
tool works over the socket, and the write tools are absent.

## Units

### 01 — bridge-command

- **Approach:** new `src/campaign_logger/bridge.py` renders the two unit files
  from the running installation's absolute path to `campaign-logger` (not a
  fixed path) and wraps `systemctl --user`. `cli.py` registers a `bridge` group
  with `start`, `stop` and `status`; each prints what it is about to do before
  it does it. Where `systemctl --user` is unavailable the commands exit non-zero
  with one line saying so and fall back to nothing. No credential is copied into
  a unit file: the service runs as the owner and reads `~/.campaign_logger.json`
  as `campaign-logger mcp` already does.
- **Scope:** `src/campaign_logger/bridge.py` (new), `src/campaign_logger/cli.py`
  (register the group only), `tests/test_bridge.py` (new).
- **Out of scope:** `mcp_server.py`, `api.py`, existing tests, dependencies, CI,
  docs (unit 02), the sandbox tooling.
- **Acceptance criteria:** `tox -e check` and `tox -e py314-cover` pass; tests
  show the units contain the socket path, `SocketMode=0600`,
  `DirectoryMode=0700`, `Accept=yes` and no `--write`; `bridge start` writes the
  files, reloads and enables, and `bridge stop` disables, as `systemctl` calls
  in that order; a client over the stand-in socket lists only read tools and
  gets `get_tag_types` back; calling a write tool is refused.
- **Depends on:** none

### 02 — bridge-docs

- **Approach:** add a "Bridge for sandboxes" section to
  `docs/mcp_integration.rst` and a short pointer in `docs/mcp-server.md`. It
  states what `bridge start` will write and enable before the reader runs it,
  how to check it, how to remove it (`bridge stop`, delete the two unit files,
  `systemctl --user daemon-reload`), and that it is read-only. It shows the
  sandbox-side `socat STDIO UNIX-CONNECT:/run/mcp/campaign-logger.sock` line and
  links the hub for the sandbox setup. It describes Campaign Logger as a
  structured database for planning roleplaying games.
- **Scope:** `docs/mcp_integration.rst`, `docs/mcp-server.md`, and
  `CHANGELOG.rst` only if its form shows a place for an unreleased entry.
- **Out of scope:** code, tests, the hub's documents.
- **Acceptance criteria:** `tox -e check` and `tox -e docs` pass.
- **Depends on:** 01

## Cost

**0 Jules sessions.** Jules has been read-only since 2026-11-11, so nothing in
this plan is dispatched to it, and no unit counts against the ten-session
ceiling in `.claude/reference/local-conventions.md`. Both units are `claude`
units, worked in-session. Antigravity quota, were it used later, is not a Jules
session either.

## Success test

On a machine where Campaign Logger is installed,
`systemctl --user list-unit-files 'campaign-logger-bridge*'` shows nothing
enabled and no socket exists. After `campaign-logger bridge start`, the
unchanged sandbox-side `socat STDIO UNIX-CONNECT:/run/mcp/campaign-logger.sock`
reaches a server whose tool list has no write tool. After `bridge stop` the
socket is gone.

## Blast radius

Low. The change adds a command group and a module, and changes nothing about
`campaign-logger mcp`. If the units are wrong the failure is a bridge that does
not start or that starts the wrong command, which `bridge stop` removes. The
serious failure is exposing write tools or a credential: that is why the service
line is asserted free of `--write` by a test, and the socket mode and directory
mode are asserted too. Undo is `bridge stop` plus deleting the two unit files;
reverting the PR removes the command.

## Sensitive paths

From `.claude/reference/local-conventions.md`, any diff touching these escalates
to a human: `src/campaign_logger/cli.py` (it handles credentials; unit 01 edits
it to register the group only), `src/campaign_logger/mcp_server.py` and `api.py`
(not to be touched), `pyproject.toml`, `uv.lock`, `setup.cfg`, `tox.ini`, `ci/`,
`.github/`, `AGENTS.md`, `.claude/`. Added for this plan: any **new** file that
writes under `~/.config/systemd/` or opens a socket, which `bridge.py` does, so
it is reviewed by a human even though it is new.

## Risks and unknowns

- Whether `%t/agent-sandbox/mcp/` is created with `DirectoryMode=0700` by the
  `.socket` unit for the intermediate directory, or only for the last component.
  The unit-01 implementer must check `systemd.socket(5)` and, if needed, create
  the parent with mode `0700` in `bridge start`.
- The stand-in accept loop is not systemd. It proves the server behaves over a
  socket, not that the units load. A human must run `bridge start` once on a
  real user manager; this is a manual step in the PR description.
- Locating the installation's `campaign-logger` executable (`shutil.which` vs
  `sys.argv[0]`) when run under `uv run` or a venv is a guess until tried.
- Hub plan 570's own prompt for this unit (`prompts/570-07-…`, possibly
  renumbered) may change while its PR is under review; this plan does not track
  it.
- Whether `assignee: agent` becomes valid is unknown.

## Not doing

- Starting anything at login or install time.
- A network or HTTP transport
  ([#159](https://github.com/Ciemaar/campaign_logger/issues/159)).
- A write socket.
- Changes to the sandbox tooling, which lives in the hub.
- Non-systemd platforms: `bridge` exits non-zero with one line there.

## Outcome

<!-- Fill in before archiving. -->
