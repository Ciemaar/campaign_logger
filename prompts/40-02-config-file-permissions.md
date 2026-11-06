---
plan: 40
unit: 02
name: config-file-permissions
repo: Ciemaar/campaign_logger
pr:
iteration: 1
---

# 40-02 config-file-permissions — warn when the config file is readable by others

`load_config()` should check the mode of `~/.campaign_logger.json` before
reading it. If group or other bits are set (`mode & 0o077`), print a warning to
**stderr** naming the file and suggesting `chmod 600 <path>`, then load the
file anyway. Do not refuse to load it, and never write to stdout. Skip the check
on Windows (`os.name == "nt"`), where mode bits mean nothing. Do not change
where the loaded values go (a later unit does that) or any option declaration.

Document in `docs/usage.rst` and `docs/mcp-server.md`, next to the existing
config-file instructions, that the file holds secrets and should be mode 0600.

# Scope

**Modify only these files:**

- `src/campaign_logger/cli.py` (`load_config` only)
- `tests/test_config_permissions.py` (new)
- `docs/usage.rst`
- `docs/mcp-server.md`

**Also in scope, always:** `reports/40-02-config-file-permissions.md`, your report.
It is never counted against the file list above.

**Do not modify:** existing tests, dependency manifests, CI configuration, the
agents' own instruction files (`AGENTS.md`, `.claude/`), any plan or prompt file,
or anything not listed above. If the task appears to require a file outside
scope, stop and say so in the PR description instead.

# Conventions

**Read `AGENTS.md` at the repo root before writing any code.** Line length is
140, imports are sorted by `ruff`, tests use `pytest` fixtures, external calls are
mocked with `requests-mock`, and CLI tests use `click.testing.CliRunner`.

Reference: `load_config()` in `src/campaign_logger/cli.py` resolves
`Path.home() / ".campaign_logger.json"`. Existing tests isolate the home
directory; read `tests/conftest.py` for how, and use `monkeypatch.setattr(Path,
"home", ...)` or `tmp_path` the same way. `create_mcp_server()` calls
`load_config()` and the MCP server uses **stdout as its protocol channel**.

# Acceptance criteria

- [ ] the new tests show a file with mode `0o644` warns on **stderr** with the path and `chmod 600`, still loads its values, writes nothing to stdout, and a `0o600` file warns about nothing
- [ ] `tox -e check` passes
- [ ] `tox -e py314-cover` passes (it enforces `--cov-fail-under=95`)
- [ ] **the report contains the verbatim output of every check above**, pasted
  as text, not a statement that they were run and not a summary

Your VM clones the repository and installs dependencies, so **run these; do not
reason about what they would print.** CI is not runnable there; the reviewer
verifies it. Do not claim green checks you have not seen. If a check cannot run
in your environment, say so in the PR description rather than simulating it.

# Anti-goals

- Do not add dependencies.
- Do not restructure modules or move files.
- Do not modify or weaken existing tests to make them pass.
- Do not reformat untouched code.
- Do not expand scope to "while I was in there" fixes.
- Do not modify anything under `.github/`, and do not edit the generated
  `tox.ini`.
- Never print, log or commit a real credential. Use obviously fake values.

# Before you finish

Run the checks above. If one fails, fix the cause; never by weakening a test,
deleting an assertion, disabling a hook or excluding a file. If a check fails for
a reason your change did not cause, say so in the PR description and name the
evidence.

Write `reports/40-02-config-file-permissions.md` from `reports/TEMPLATE.md` (Part 1 only),
then run `pre-commit run --all-files` last, `git add -u`, add the report, and
repeat until clean. The output you pasted is from the earlier run; that is
expected.

# Test integrity

Existing tests are the specification. If an existing test fails, the change is
wrong; do not edit the test. If a test appears genuinely incorrect, leave it
failing and explain why in the PR description. New tests for new behaviour are
welcome.

# Answering questions

If the reviewer asks you something, answer in the pull request, by pushing a
commit or replying in the PR thread. Your session conversation is not visible to
the reviewer.

# PR description

Include which plan and unit this implements (`plan 40, unit 02`), what
changed and why, anything you were unsure about, anything you left alone because
it was out of scope, and anything that should become a GitHub issue (you cannot
open one; describe it so the reviewer can).
