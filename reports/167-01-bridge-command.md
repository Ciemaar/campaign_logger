---
plan: 167
unit: 01
name: bridge-command
prompt: /prompts/167-01-bridge-command.md
iteration: 2
author: claude
reviewer: human
session: https://claude.ai/code/session_01EQrwqWNQndN1deQdS14gdE
pr: 174
verdict:
opened: 2026-11-18
reviewed:
partial:
---

# Report 167-01 — bridge-command

- **Diff:** `4 files changed, 701 insertions(+), 1 deletion(-)` (code and
  tests), plus this report, and the plan and prompts (see Deviations)
- **Prompt:** `/prompts/167-01-bridge-command.md`
- **Implemented by:** claude — **Verified by:** human (see Part 2)

______________________________________________________________________

## Part 1 — Implementation record

### What changed, and why

`src/campaign_logger/bridge.py` renders two systemd user units and wraps
`systemctl --user`. The units are `campaign-logger-bridge.socket`, which
listens at `%t/campaign-logger-mcp-ro/campaign-logger.sock` with
`SocketMode=0600`, `DirectoryMode=0700`, `RemoveOnStop=yes` and `Accept=yes`,
and `campaign-logger-bridge@.service`,
which runs `<this installation's campaign-logger> mcp` with stdin and stdout on
the socket. The sandbox keeps connecting the way it does today, and nothing
idles between connections. `bridge start` prints what it will do, writes the
files under `$XDG_CONFIG_HOME/systemd/user` (by default
`~/.config/systemd/user`) only where they differ, then runs `daemon-reload` and
`enable --now`. `bridge stop` runs `disable --now`. `bridge status` reports
`is-active` and the socket path. Installing the package enables nothing.

The click group is defined in `bridge.py`, and `cli.py` only imports it and
calls `main.add_command(bridge)`. That keeps the `cli.py` edit, a sensitive
path, to registering the group, as the prompt allows. No credential reaches a
unit file; a test asserts the rendered text contains no `Environment`, `CL_`,
`token`, `secret` or `client`.

**Iteration 2 (2026-11-20), from the owner's hand run in the #168 comments.**
The socket's directory, `campaign-logger-mcp-ro`, holds that socket alone and
sits directly under `$XDG_RUNTIME_DIR`, so a sandbox mounts it read-only and a
later write socket, in a directory of its own, cannot be reached through the
same mount. It is the directory the hand-run bridge already uses and the
sandbox already mounts. `bridge start` now calls `ensure_socket_dir()` before
writing any unit: it creates the directory `0700`, tightens one of the user's
own that is too open, and stops with one line when the directory cannot be
created, is not a directory (a file or a symlink), or belongs to another user.
The last is what happened on the owner's machine, where Docker had made the old
`agent-sandbox` directory `root:root 0755`; `DirectoryMode=` only applies to
directories systemd creates, so it could not have caught it. `RemoveOnStop=yes`
makes `bridge stop` remove the socket file, which its message already claimed.

### Criteria as claimed

<!-- mdformat off -->

| #   | criterion | command run | claimed result |
| --- | --------- | ----------- | -------------- |
| 1   | `tox -e check` passes | `tox -e check` (clean worktree at the PR head) | `check: OK`, `congratulations :)` |
| 2   | `tox -e py314-cover` passes with the floor | `tox -e py314-cover` | `510 passed, 12 skipped`; `Total coverage: 97.44%`; `bridge.py` 99.26% (the non-POSIX branch of the ownership check) |
| 3   | socket unit has path, `0600`, `0700`, `Accept=yes`; service has `campaign-logger … mcp`, no `--write` | `test_socket_unit_listens_where_the_sandbox_expects_with_private_modes`, `test_service_runs_this_installation_read_only` | PASSED |
| 4   | `start` writes both files, then `daemon-reload`, then `enable --now`; `stop` calls `disable --now` | `test_start_writes_units_then_reloads_then_enables`, `test_start_says_what_it_will_do_before_doing_it`, `test_stop_disables` | PASSED |
| 5   | stand-in accept loop, `0600` socket in `0700` dir, `get_tag_types` works, no write tools, write call refused | `test_read_tool_works_over_the_socket_and_write_tools_are_absent` | PASSED (ran, not skipped, on Linux) |
| 6   | missing `systemctl` exits non-zero with one line | `test_without_systemctl_exits_non_zero_with_one_line[start/stop/status]` | PASSED |
| —   | (#168 finding) `start` creates and checks its own directory; one line when it cannot | `test_start_creates_the_socket_directory_private`, `test_an_existing_directory_of_ours_is_tightened`, `test_a_directory_owned_by_someone_else_stops_start_with_one_line`, `test_a_directory_that_cannot_be_created_stops_start_with_one_line`, `test_a_file_in_the_way_is_refused`, `test_a_symlink_in_the_way_is_refused`, `test_no_runtime_dir_is_refused` | PASSED |
| 7   | report carries verbatim check output | this section | below |

<!-- mdformat on -->

### Local checks at PR-open

These were run in a clean `git worktree` at the PR head. The main checkout
holds many untracked generated files, and `ruff` and `pyright` would scan them.

<!-- mdformat off -->

| check | command | result |
| ----- | ------- | ------ |
| tests | `tox -e py314-cover` | `510 passed, 12 skipped, 3 warnings in 6.11s`; `Required test coverage of 95% reached. Total coverage: 97.44%` |
| lint | `ruff check .` (in `tox -e check`) | `All checks passed!` |
| formatting | `ruff format --check .` (in `tox -e check`) | `70 files already formatted` |
| types | `pyright .` (in `tox -e check`) | `0 errors, 0 warnings, 0 informations` |
| packaging | build, `twine check`, `check-manifest` (in `tox -e check`) | pass; `check: OK (25.53=…)`, `congratulations :)` |
| docs | `tox -e docs` | exit 0 |
| pre-commit | `pre-commit run --files <the four changed files>` | **fails before checking anything**: the hook's pinned `ruff` rejects `target-version = "py314"` (`unknown variant py314, expected one of … py313`). This comes from `.pre-commit-config.yaml` and happens on `main` too, so this change did not cause it. I left the file alone because it is out of scope and a sensitive path. |

<!-- mdformat on -->

Verbatim `tests/test_bridge.py -v`:

```text
tests/test_bridge.py::test_socket_unit_listens_where_the_sandbox_expects_with_private_modes PASSED [  3%]
tests/test_bridge.py::test_service_runs_this_installation_read_only PASSED [  7%]
tests/test_bridge.py::test_service_carries_no_credential PASSED          [ 10%]
tests/test_bridge.py::test_service_quotes_a_path_systemd_would_split_or_expand PASSED [ 14%]
tests/test_bridge.py::test_executable_is_the_one_on_path PASSED          [ 17%]
tests/test_bridge.py::test_executable_falls_back_to_the_running_script PASSED [ 21%]
tests/test_bridge.py::test_unit_dir_defaults_under_home PASSED           [ 25%]
tests/test_bridge.py::test_socket_path_without_runtime_dir_names_the_variable PASSED [ 28%]
tests/test_bridge.py::test_the_socket_directory_is_its_own PASSED        [ 32%]
tests/test_bridge.py::test_write_units_leaves_unchanged_files_alone PASSED [ 35%]
tests/test_bridge.py::test_start_writes_units_then_reloads_then_enables PASSED [ 39%]
tests/test_bridge.py::test_start_says_what_it_will_do_before_doing_it PASSED [ 42%]
tests/test_bridge.py::test_stop_disables PASSED                          [ 46%]
tests/test_bridge.py::test_status_reports_state_and_path PASSED          [ 50%]
tests/test_bridge.py::test_without_systemctl_exits_non_zero_with_one_line[start] PASSED [ 53%]
tests/test_bridge.py::test_without_systemctl_exits_non_zero_with_one_line[stop] PASSED [ 57%]
tests/test_bridge.py::test_without_systemctl_exits_non_zero_with_one_line[status] PASSED [ 60%]
tests/test_bridge.py::test_failing_systemctl_surfaces_its_first_line PASSED [ 64%]
tests/test_bridge.py::test_failing_systemctl_with_no_output_names_the_status PASSED [ 67%]
tests/test_bridge.py::test_start_creates_the_socket_directory_private PASSED [ 71%]
tests/test_bridge.py::test_an_existing_directory_of_ours_is_tightened PASSED [ 75%]
tests/test_bridge.py::test_a_directory_owned_by_someone_else_stops_start_with_one_line PASSED [ 78%]
tests/test_bridge.py::test_a_directory_that_cannot_be_created_stops_start_with_one_line PASSED [ 82%]
tests/test_bridge.py::test_a_file_in_the_way_is_refused PASSED           [ 85%]
tests/test_bridge.py::test_a_symlink_in_the_way_is_refused PASSED        [ 89%]
tests/test_bridge.py::test_no_runtime_dir_is_refused PASSED              [ 92%]
tests/test_bridge.py::test_bridge_is_registered_on_the_main_cli PASSED   [ 96%]
tests/test_bridge.py::test_read_tool_works_over_the_socket_and_write_tools_are_absent PASSED [100%]
============================== 28 passed in 1.07s ==============================
```

Verbatim `tox -e check` tail:

```text
check: commands[3]> ruff check .
All checks passed!
check: commands[4]> ruff format --check .
70 files already formatted
check: commands[5]> pyright .
0 errors, 0 warnings, 0 informations
check: commands[6]> mdformat --check --wrap 80 README.md SESSION_INSTRUCTIONS.md PYPI_UPLOAD_INSTRUCTIONS.md AGENTS.md .github/copilot-instructions.md docs/tooling_evaluation.md
check: commands[7]> rstfmt --check AUTHORS.rst CONTRIBUTING.rst README.rst CHANGELOG.rst docs/usage.rst docs/reference/index.rst docs/installation.rst docs/readme.rst docs/contributing.rst docs/authors.rst docs/changelog.rst docs/index.rst
  check: OK (25.53=setup[0.02]+cmd[8.21,0.38,9.15,0.02,0.03,6.34,0.37,1.02] seconds)
  congratulations :) (25.58 seconds)
```

### Deviations from the prompt

- **An existing test was modified, with the owner's approval.**
  `tests/test_cli_exit_codes.py` walks every leaf command and requires a
  non-zero exit when the API fails. The bridge commands never call the API, so
  `bridge status` failed it, and the test also reached the real `systemctl` on
  the implementing machine (a read-only `is-active`). The owner chose to extend
  the file's existing `NOT_CLIENT_BACKED` exemption, which already lists `mcp`
  for the same reason, to the three bridge commands. No assertion was weakened.
- **The plan and prompts were edited on this branch**, which the prompt says not
  to do. `bee0ce3` records unit 01's state (`in-review`, `pr: 174`, the
  report), which is the orchestrator's bookkeeping. The 2026-11-20 commit
  records the directory-per-socket revision in the plan and in prompts 02 and
  03, and fixes stale numbering: docs are unit 03, there are three units, and
  removal deletes up to four unit files. The owner asked, through the hub
  session, for the #168 findings to be handled on this PR.
- **The socket path differs from the prompt's**
  (`agent-sandbox/mcp/campaign-logger.sock` there). The prompt's "the sandbox
  must not need to change" no longer holds: the sandbox was moved by hand to
  mount `campaign-logger-mcp-ro`, and this follows it.
- **The MCP client in the socket test is a minimal newline-delimited JSON-RPC
  client** (`initialize`, `notifications/initialized`, `tools/list`,
  `tools/call`). The `mcp` SDK client was not used: wiring its anyio streams to
  a raw unix socket would have added more machinery than it tests.
- The service also sets `StandardError=journal`, so server errors go to the
  journal rather than onto the socket, where they would corrupt the JSON-RPC
  stream. Both units carry `[Unit] Description=`, and the socket has
  `[Install] WantedBy=sockets.target`, without which `enable` has nothing to
  install.
- `ExecStart` quotes the executable path when it contains whitespace, quotes or
  backslashes, and doubles `%`.
- The prompt says docs are "unit 02". Docs are unit 03 since the plan was
  revised, and this unit touches no docs.

### Left undone

- **A human must run `campaign-logger bridge start` once on a real user
  manager.** The tests mock `systemctl` and stand in for systemd. They prove the
  server works over a socket, not that the units load. If the interim `socat`
  bridge is still listening at the same path, stop it first.
- The socket test is skipped on Windows (no `AF_UNIX` with fd inheritance). On
  macOS it runs under a short `/tmp` base because of the 104-byte socket path
  limit; it has only been run locally on Linux.

### Uncertain about

- `executable()` prefers `shutil.which("campaign-logger")`. Under `uv run` that
  is the project venv's script. From a shell where another `campaign-logger` is
  earlier on `PATH` (for example `~/.local/bin`), the unit pins that one
  instead. `bridge start` prints the path it will use before acting, so the
  user can see which.
- `bridge stop` leaves the unit files in place, as the plan's undo path
  describes, and says how to remove them.
- The ownership check is skipped off POSIX (no `getuid`). That only matters in
  tests: without systemd the commands stop at the missing `systemctl`.
- Whether systemd unlinks a stale socket file left by the hand-run `socat` at
  the same path, or fails to bind. Either way, stop that `socat` first.

______________________________________________________________________

## Part 2 — Independent verification

The implementer was Claude, so there is no independent agent reviewer. The
owner's review happens in the PR comments.
