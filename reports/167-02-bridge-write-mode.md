---
plan: 167
unit: 02
name: bridge-write-mode
prompt: /prompts/167-02-bridge-write-mode.md
iteration: 1
author: claude
reviewer: human
session: https://claude.ai/code/session_01EQrwqWTKhaaQASKkvzhmr5
pr:
verdict:
opened: 2026-11-26
reviewed:
partial:
---

# Report 167-02 — bridge-write-mode

- **Diff:** `2 files changed, 498 insertions(+), 51 deletions(-)` (code and
  tests), plus this report
- **Prompt:** `/prompts/167-02-bridge-write-mode.md`
- **Implemented by:** claude — **Verified by:** human (see Part 2)

______________________________________________________________________

## Part 1 — Implementation record

### What changed, and why

`bridge.py` now describes a socket and service pair as a frozen `Mode`: the
read-only pair unit 01 shipped (`READ`) and a second, independent write pair
(`WRITE`). The rendering, directory, socket-free and `systemctl` helpers take a
`Mode` that defaults to `READ`, so they are parameterised and not copied, and
the read units render the same text as before (a test pins unit 01's text in
full). `WRITE` is `campaign-logger-bridge-write.socket` and
`campaign-logger-bridge-write@.service`, listening at
`%t/campaign-logger-mcp-rw/campaign-logger-write.sock` in a directory of its own
that is never the read socket's, with the same `0700`, `0600`, `Accept=yes` and
`RemoveOnStop=yes`; its service runs `<exe> mcp --write`. `start`, `stop` and
`status` take `--write`, which selects the write pair alone; without it they
never name a write unit, except that `status` also reports the write socket so
an open one is never hidden. `start --write` prints the socket and that a
connected agent can create, update and delete campaign data with the owner's
credentials, before any check or `systemctl` call. It does not prompt. Nothing
adds a default, a config option or an environment variable that starts the write
socket or makes the read socket serve write tools.

### Criteria as claimed

<!-- mdformat off -->

| #   | criterion | command run | claimed result |
| --- | --------- | ----------- | -------------- |
| 1   | `tox -e check` passes | `uvx tox -e check` | `check: OK` |
| 2   | `tox -e py314-cover` passes, including the coverage floor | `uvx tox -e py314-cover` | `534 passed, 12 skipped`; `Required test coverage of 95% reached. Total coverage: 97.27%` |
| 3   | read units byte-identical to unit 01's | `test_the_read_units_are_byte_identical_to_unit_01s` | pass |
| 4   | write socket's directory differs from the read socket's | `test_the_write_socket_has_a_directory_of_its_own` | pass |
| 5   | write socket unit has the write path, `SocketMode=0600`, `DirectoryMode=0700`, `Accept=yes`; write service ends `mcp --write` | `test_the_write_units_name_the_write_socket_and_run_the_write_server` | pass |
| 6   | `start` without `--write` names no write unit; `start --write` and `stop --write` name no read unit | `test_start_without_write_never_names_a_write_unit`, `test_stop_without_write_never_names_a_write_unit`, `test_start_write_makes_the_expected_calls_on_the_write_unit_only`, `test_stop_write_disables_the_write_unit_only` | pass |
| 7   | `start --write` prints the path and that agents can change data, before the first `systemctl` call | `test_start_write_says_what_it_does_before_the_first_systemctl_call` | pass |
| 8   | `bridge status` reports both sockets | `test_status_reports_both_sockets_labelled` and two siblings | pass |
| 9   | over the in-test accept loop with `mcp --write`: write tool listed and a write call succeeds against a stubbed API; the read stand-in lists none | `test_the_write_socket_lists_write_tools_and_a_write_call_works_while_the_read_socket_still_has_none` | pass |

<!-- mdformat on -->

### Local checks at PR-open

Run in a checkout of the branch at the commit that carries this report.

<!-- mdformat off -->

| check      | command                  | result |
| ---------- | ------------------------ | ------ |
| tests      | `uvx tox -e py314-cover` | `================= 534 passed, 12 skipped, 3 warnings in 9.86s ==================` |
| coverage   | same run                 | `Required test coverage of 95% reached. Total coverage: 97.27%` |
| lint       | `uvx tox -e check` (ruff)| clean |
| types      | `uvx tox -e check` (pyright) | `0 errors, 0 warnings, 0 informations` |
| formatting | `uvx tox -e check` (ruff format, mdformat, rstfmt) | `check: OK` |

<!-- mdformat on -->

Verbatim tail of the final `tox -e check` run:

```
check: commands[5]> pyright .
0 errors, 0 warnings, 0 informations
check: commands[6]> mdformat --check --wrap 80 README.md SESSION_INSTRUCTIONS.md PYPI_UPLOAD_INSTRUCTIONS.md AGENTS.md .github/copilot-instructions.md docs/tooling_evaluation.md
check: commands[7]> rstfmt --check AUTHORS.rst CONTRIBUTING.rst README.rst CHANGELOG.rst docs/usage.rst docs/reference/index.rst docs/installation.rst docs/readme.rst docs/contributing.rst docs/authors.rst docs/changelog.rst docs/index.rst
  check: OK (40.41=setup[0.02]+cmd[15.81,0.97,9.81,0.02,0.03,10.99,0.52,2.24] seconds)
  congratulations :) (40.47 seconds)
```

Verbatim tail of the final `tox -e py314-cover` run:

```
SKIPPED [1] tests/test_e2e.py:143: need --run-live-read option to run
SKIPPED [4] tests/test_live_read.py: need --run-live-read option to run
SKIPPED [6] tests/test_live_read.py:65: need --run-live-read option to run
================= 534 passed, 12 skipped, 3 warnings in 9.86s ==================
  py314-cover: OK (13.59=setup[2.34]+cmd[11.26] seconds)
  congratulations :) (13.73 seconds)
```

Unit 01's 31 tests pass unchanged: the diff to `tests/test_bridge.py` is 352
insertions and no deletions. A mutation check, with the write service's
`--write` temporarily removed from `render_service`, made
`test_the_write_units_name_the_write_socket_and_run_the_write_server` and the
over-the-socket test fail; the change was reverted.

The earlier `tox -e check` run failed on two E501 lines I had written (one in
`bridge.py`, one in the new tests); both are wrapped and the run above is clean.

### Deviations from the prompt

- **`cli.py` is not touched.** The prompt lists it for the `--write` option, but
  unit 01 put the `bridge` group and its commands in `bridge.py` and `cli.py`
  only registers the group, so the option belongs in `bridge.py`. That also
  keeps a credential-handling file out of the diff.
- **`status` without `--write` asks systemd about the write unit only when it
  could exist** (its unit file is installed, or its socket file is present);
  otherwise it prints `campaign-logger-bridge-write.socket: not installed` with
  no `systemctl` call. Unit 01's status test asserts that exactly one
  `systemctl` call is made, and the prompt forbids changing it. A write socket
  that is open is still reported, including when its unit file was deleted.
- **`start --write` prints its disclosure before the directory and socket
  checks**, so it precedes the first `systemctl` call. If a check then refuses,
  the output is the disclosure followed by one `Error:` line.
- **`RemoveOnStop=yes` is on the write socket too**, as on the read one; the
  prompt's sketch omits it. It is what makes `stop --write` remove the socket.

### Left undone

- The units were not loaded under a real systemd. A human must run
  `campaign-logger bridge start --write` once on a real user manager, check
  `campaign-logger bridge status`, and run `bridge stop --write` afterwards.
- Documentation is unit 03's.

### Uncertain about

- Whether a disclosure line followed by an `Error:` line is acceptable when a
  check refuses `start --write`. The alternative is to run the checks first,
  which would put a `systemctl is-active` call ahead of the disclosure.
- Whether a user manager will start `campaign-logger-bridge-write@.service` with
  `ExecStart=… mcp --write` exactly as it does the read service. The stand-in
  accept loop shows the server behaves over a socket, not that the units load.

### Sensitive paths touched

`src/campaign_logger/bridge.py`: a file that writes under
`~/.config/systemd/` and opens sockets, named in the plan's sensitive paths.
No other sensitive path (`cli.py`, `mcp_server.py`, `api.py`, `pyproject.toml`,
`uv.lock`, `setup.cfg`, `tox.ini`, `ci/`, `.github/`, `AGENTS.md`, `.claude/`)
is in the diff.

______________________________________________________________________

## Part 2 — Independent verification

The implementer is Claude, so there is no independent agent reviewer. See the PR
comments.
