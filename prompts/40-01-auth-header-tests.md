---
plan: 40
unit: 01
name: auth-header-tests
repo: Ciemaar/campaign_logger
pr:
iteration: 1
---

# 40-01 auth-header-tests — pin which auth headers each client sends

Add tests that assert, on the request actually received by a `requests-mock`
adapter, exactly which authentication headers each client sends. The tests are
the point: they must fail if a header is dropped, renamed or sent when it should
not be. Do not change `src/`.

Assert: `GeneratorClient(token=...)` sends `Authorization: Bearer <token>`;
`LoggerClient(client_id=..., client_secret=...)` sends `api-client` and
`api-secret` with those values; `GeneratorClient()` sends no `Authorization`;
`LoggerClient()` and a `LoggerClient` given only one of the two values send
neither `api-client` nor `api-secret`.

The issue (#41) says four `# pragma: no cover` directives hid this code from
the coverage gate. Check whether any remain in `src/campaign_logger/api.py`; if
none do, say so in your report and change nothing there. Do not add any.

# Scope

**Modify only these files:**

- `tests/test_auth_headers.py` (new)

**Also in scope, always:** `reports/40-01-auth-header-tests.md`, your report.
It is never counted against the file list above.

**Do not modify:** existing tests, dependency manifests, CI configuration, the
agents' own instruction files (`AGENTS.md`, `.claude/`), any plan or prompt file,
or anything not listed above. If the task appears to require a file outside
scope, stop and say so in the PR description instead.

# Conventions

**Read `AGENTS.md` at the repo root before writing any code.** Line length is
140, imports are sorted by `ruff`, tests use `pytest` fixtures, external calls are
mocked with `requests-mock`, and CLI tests use `click.testing.CliRunner`.

Reference, in `src/campaign_logger/api.py`: `GeneratorClient.__init__` sets
`Authorization: Bearer <token>` on `self.session.headers` only `if token`;
`LoggerClient.__init__` sets `api-client` and `api-secret` only
`if client_id and client_secret`. Existing example of asserting on the request
actually sent: `tests/test_redirect_auth.py`. Use `requests-mock`.

# Acceptance criteria

- [ ] `pytest tests/test_auth_headers.py --cov=campaign_logger.api --cov-report=term-missing` passes and the `if token:` and `if client_id and client_secret:` blocks in `api.py` are not listed under Missing
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

Write `reports/40-01-auth-header-tests.md` from `reports/TEMPLATE.md` (Part 1 only),
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

Include which plan and unit this implements (`plan 40, unit 01`), what
changed and why, anything you were unsure about, anything you left alone because
it was out of scope, and anything that should become a GitHub issue (you cannot
open one; describe it so the reviewer can).
