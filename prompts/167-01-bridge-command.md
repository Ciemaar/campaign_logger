---
plan: 167
unit: 01
name: bridge-command
repo: Ciemaar/campaign_logger
pr:
iteration: 1
---

# 167-01 bridge-command — `campaign-logger bridge start|stop|status` for a systemd user socket

Add a `bridge` command group that opens, closes and reports a unix socket
serving the **read-only** MCP server to sandboxed agents. Read
[issue #167](https://github.com/Ciemaar/campaign_logger/issues/167) first; it
carries the requirements. **Installing the package must start and enable
nothing.** The socket stays closed until `bridge start`; `bridge stop` closes
it.

Today the bridge is a hand-typed host command that dies with its shell:

```bash
socat UNIX-LISTEN:"$XDG_RUNTIME_DIR"/agent-sandbox/mcp/campaign-logger.sock,fork,mode=600,unlink-early \
  EXEC:"$HOME/Dropbox/campaign_logger/.venv/bin/campaign-logger mcp"
```

The sandbox side connects with
`socat STDIO UNIX-CONNECT:/run/mcp/campaign-logger.sock` and **must not need to
change**: keep the path
`$XDG_RUNTIME_DIR/agent-sandbox/mcp/campaign-logger.sock`, directory mode
`0700`, socket mode `0600`.

# Scope

**Modify only these files:**

- `src/campaign_logger/bridge.py` (new: unit rendering and the `systemctl`
  calls)
- `src/campaign_logger/cli.py` (register the `bridge` group; nothing else)
- `tests/test_bridge.py` (new)

**Also in scope, always:** `reports/167-01-bridge-command.md`, written from
`reports/TEMPLATE.md`, Part 1 only, before you open the PR.

**Do not modify:**

- existing tests
- `src/campaign_logger/mcp_server.py`, `src/campaign_logger/api.py`
- `pyproject.toml`, `uv.lock`, `setup.cfg`, `tox.ini`, `ci/`, `.github/`,
  `AGENTS.md`, `.claude/`
- docs (unit 02 does them)
- any plan or prompt file
- anything not listed above

If the task appears to require a file outside scope, stop and say so in the PR
description instead of doing it.

# Design (decided; do not choose differently)

- **Two systemd user units**, rendered as text:

  ```ini
  # campaign-logger-bridge.socket
  [Socket]
  ListenStream=%t/agent-sandbox/mcp/campaign-logger.sock
  SocketMode=0600
  DirectoryMode=0700
  Accept=yes

  # campaign-logger-bridge@.service
  [Service]
  ExecStart=<absolute path to this installation's campaign-logger> mcp
  StandardInput=socket
  StandardOutput=socket
  ```

  `%t` is `$XDG_RUNTIME_DIR`. Render the executable path from the running
  installation (`shutil.which("campaign-logger")` falling back to the resolved
  `sys.argv[0]`), never a fixed path. The service line must not contain
  `--write`. Verify against `systemd.socket(5)` whether `DirectoryMode` covers
  the intermediate `agent-sandbox` directory; if not, `bridge start` creates it
  with mode `0700` first.

- **`bridge start`** prints what it is about to do, writes the two files under
  `~/.config/systemd/user/` if they differ, runs
  `systemctl --user daemon-reload`, then
  `systemctl --user enable --now campaign-logger-bridge.socket`.
  **`bridge stop`** prints, then runs `systemctl --user disable --now` on the
  same unit. **`bridge status`** prints whether the socket unit is active and
  the socket path.

- **Read-only only.** No write socket.

- **Secrets stay on the host.** Never copy a credential into a unit file or an
  environment line; the service reads `~/.campaign_logger.json` as
  `campaign-logger mcp` does.

- **Without `systemctl --user`** the commands exit non-zero with one line saying
  so. No fallback.

# Conventions

**Read `AGENTS.md` first.** Line length 140, ruff and pyright, Python 3.14.

How a command is declared and how errors surface (from
`src/campaign_logger/cli.py`, function `mcp`):

```python
@main.command()
@click.option("--write", is_flag=True, help="Run the MCP server with write tools enabled")
def mcp(write):
    """Start the Campaign Logger MCP server."""
    from .mcp_server import run_mcp_server

    try:
        run_mcp_server(read_only=not write)
    except EXPECTED_ERRORS as e:
        raise click.ClickException(f"MCP server failed: {e}") from e
```

Tests use `click.testing.CliRunner`; mock `subprocess.run` so no test touches
the real user manager. Existing server tests (`tests/test_mcp.py`) list tools
with `asyncio.run(server.list_tools())`.

# Acceptance criteria

- [ ] `tox -e check` passes
- [ ] `tox -e py314-cover` passes, including the coverage floor
- [ ] a test asserts the rendered socket unit contains the socket path,
  `SocketMode=0600`, `DirectoryMode=0700` and `Accept=yes`, and that the
  rendered service contains `campaign-logger` followed by `mcp` and not
  `--write`
- [ ] a test asserts `bridge start` writes both files, then calls
  `daemon-reload`, then `enable --now`, in that order, and `bridge stop` calls
  `disable --now`
- [ ] a test stands in for systemd with an in-test accept loop that runs one
  `campaign-logger mcp` subprocess per connection on a `0600` socket in a `0700`
  directory, connects an MCP client, calls `get_tag_types` (needs no
  credentials) successfully, and shows the tool list has no write tool and a
  write call is refused
- [ ] a test asserts exit non-zero with one line when `systemctl` is missing
- [ ] the report contains the verbatim output of every check above, as text

# Anti-goals

- No new dependencies. No changes to `mcp_server.py`. No autostart. No network
  listener. No weakening of existing tests.
- Do not claim the units load under a real systemd: say in the PR description
  that a human must run `bridge start` once on a real user manager.

# Before you finish

Run the checks, write the report, then rerun `tox -e check` so the report is
formatted. Fix causes, never weaken a test.

# Test integrity

Do not modify or delete existing tests. New tests only.

# Answering questions

Put questions in the PR description.
