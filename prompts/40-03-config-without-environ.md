---
plan: 40
unit: 03
name: config-without-environ
repo: Ciemaar/campaign_logger
pr:
iteration: 1
---

# 40-03 config-without-environ — stop copying secrets into os.environ

Make `load_config()` return the config values instead of exporting the three
secrets into `os.environ`. The CLI groups and `create_mcp_server()` must then
obtain credentials from, in order: the command-line option or real environment
variable, then the config file. Keep `envvar=` on the options so a variable the
user really exported still works. The non-secret `default_campaign_id` and
`default_log_id` behaviour is unchanged; leave them as they are. Do not touch the
`--token` / `--client-secret` option declarations beyond what the new lookup
requires, and do not touch the permission check from the previous unit.

If the previous unit has not landed in your checkout, work against what is there
and say so in your report.

# Scope

**Modify only these files:**

- `src/campaign_logger/cli.py`
- `src/campaign_logger/mcp_server.py`
- `tests/test_config_no_environ.py` (new)

**Also in scope, always:** `reports/40-03-config-without-environ.md`, your report.
It is never counted against the file list above.

**Do not modify:** existing tests, dependency manifests, CI configuration, the
agents' own instruction files (`AGENTS.md`, `.claude/`), any plan or prompt file,
or anything not listed above. If the task appears to require a file outside
scope, stop and say so in the PR description instead.

# Conventions

**Read `AGENTS.md` at the repo root before writing any code.** Line length is
140, imports are sorted by `ruff`, tests use `pytest` fixtures, external calls are
mocked with `requests-mock`, and CLI tests use `click.testing.CliRunner`.

Reference: `load_config()` currently sets `os.environ["CL_GENERATOR_TOKEN"]`,
`CL_LOGGER_CLIENT_ID` and `CL_LOGGER_CLIENT_SECRET` so that Click's `envvar=`
fallback finds them; `create_mcp_server()` in `mcp_server.py` calls
`load_config()` and then reads the same variables from `os.environ`. The
`generator` and `logger` groups in `cli.py` receive them through `envvar=`.
Existing tests set credentials with `monkeypatch.setenv`; that must keep working.

# Acceptance criteria

- [ ] after `load_config()` and after a CLI invocation that took its credentials from the config file, `os.environ` contains none of `CL_GENERATOR_TOKEN`, `CL_LOGGER_CLIENT_ID`, `CL_LOGGER_CLIENT_SECRET` (new tests show it), and a real environment variable still takes precedence over the file
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

Write `reports/40-03-config-without-environ.md` from `reports/TEMPLATE.md` (Part 1 only),
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

Include which plan and unit this implements (`plan 40, unit 03`), what
changed and why, anything you were unsure about, anything you left alone because
it was out of scope, and anything that should become a GitHub issue (you cannot
open one; describe it so the reviewer can).
