---
plan: 36
unit: 01
name: bootstrap-selective-autoescape
repo: Ciemaar/campaign_logger
pr:
iteration: 1
---

# 36-01 bootstrap-selective-autoescape — never HTML-escape non-HTML templates

Replace blanket `autoescape=True` with `jinja2.select_autoescape` so the
YAML/INI templates are never HTML-escaped but Bandit B701 stays satisfied. Add a
test asserting that the environment `ci/bootstrap.py` builds does not escape
`&&`, `<`, `>` or quotes in a rendered value. The generated `tox.ini` and
workflow must be byte-identical afterwards.

If `ci/bootstrap.py` does not expose the environment for testing without running
the whole script, make the smallest change that does (for example a small
function that builds the environment) and say so in your report. Do not run
`python ci/bootstrap.py` in a way that leaves modified generated files in your
commit.

# Scope

**Modify only these files:**

- `ci/bootstrap.py` (the `jinja2.Environment(...)` construction only)
- `tests/test_bootstrap_rendering.py` (new)

**Also in scope, always:** `reports/36-01-bootstrap-selective-autoescape.md`,
your report. It is never counted against the file list above.

**Do not modify:** existing tests, dependency manifests, CI configuration, the
agents' own instruction files (`AGENTS.md`, `.claude/`), any plan or prompt
file, or anything not listed above. If the task appears to require a file
outside scope, stop and say so in the PR description instead.

# Conventions

**Read `AGENTS.md` at the repo root before writing any code.** Line length is
140, imports are sorted by `ruff`, tests use `pytest` fixtures, external calls
are mocked with `requests-mock`, and CLI tests use `click.testing.CliRunner`.

Reference, in `ci/bootstrap.py`, function `main`: the environment is constructed
with `autoescape=True` and a comment. `select_autoescape` is
`jinja2.select_autoescape(enabled_extensions=("html", "xml"), default_for_string=False, default=False)`.

# Acceptance criteria

- [ ] `python ci/bootstrap.py` then
  `git diff --exit-code -- tox.ini .github/workflows/github-actions.yml` shows
  no change, and the new test renders a template string containing `&&` and a
  quote and asserts they come out unescaped
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
deleting an assertion, disabling a hook or excluding a file. If a check fails
for a reason your change did not cause, say so in the PR description and name
the evidence.

Write `reports/36-01-bootstrap-selective-autoescape.md` from
`reports/TEMPLATE.md` (Part 1 only), then run `pre-commit run --all-files` last,
`git add -u`, add the report, and repeat until clean. The output you pasted is
from the earlier run; that is expected.

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

Include which plan and unit this implements (`plan 36, unit 01`), what changed
and why, anything you were unsure about, anything you left alone because it was
out of scope, and anything that should become a GitHub issue (you cannot open
one; describe it so the reviewer can).
