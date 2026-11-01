# Agent Instructions (Jules & Others)

This file contains instructions for AI agents working on this repository.

## Core Constraints

1. **Python Version:** Requires Python 3.14 or newer (`requires-python` in
   `pyproject.toml`). CI also tests on 3.15; do not use features newer than 3.14
   without fallbacks.
1. **Linting:** The project uses `ruff` for both linting and formatting. Run
   `ruff check .` and `ruff format .`.
1. **Type Checking:** The project uses `pyright`. Run `pyright .` to verify
   types.
1. **Testing:** Use `tox` to run tests across environments. `tox -e py314-cover`
   is preferred for fast feedback.
1. **Build System:** Uses `setuptools`. All package configuration is in
   `pyproject.toml`. `setup.cfg` holds only the `[matrix]` that
   `ci/bootstrap.py` reads.
1. **CI/CD:** Configuration is generated via `ci/bootstrap.py`. If you modify
   `setup.cfg` or `ci/templates/`, run `tox -e bootstrap`.

## Code Style

- **Line Length:** 140 characters.
- **Imports:** Sorted by `ruff` (isort).
- **Docstrings:** Google style or Sphinx style.

## Testing

- Use `pytest` fixtures.
- Mock external API calls using `requests-mock`.
- Integration tests for CLI should use `click.testing.CliRunner`.
- Suppress known security false positives in tests with `# nosec`.

## Workflow

1. Explore codebase.
1. Plan changes.
1. Implement changes.
1. Verify with `tox -e check` (lint/types) and `tox -e py314-cover` (tests).
1. **`tox.ini` and `.github/workflows/github-actions.yml` are generated.** Their
   source is `ci/templates/`, rendered by `ci/bootstrap.py` from the matrix in
   `setup.cfg`. Never edit the generated files alone -- change the template and
   run `tox -e bootstrap`, then commit both. The `bootstrap drift` CI job fails
   the build when they disagree. `.github/workflows/audit.yml` and
   `codacy.yml`-style hand-written workflows are *not* generated and have no
   template.
1. Agents should proactively monitor the tests on GitHub and autonomously
   address any CI failures (excluding codacy, which is only advisory).
1. Review the code scanning results on your PR; do not assume a green upload
   means clean results. Findings are to be **triaged, not blanket-corrected**:
   - Fix what is a genuine defect in the code you changed.
   - Leave, and say why in the PR, findings that are false positives or that
     contradict this project's own configuration. Codacy's line-length and
     import checks disagree with the `ruff` settings in `pyproject.toml`; `ruff`
     wins. Pytest fixture shadowing (`W0621`) and `assert` in tests (Bandit
     `B101`) are expected and are not defects.
   - Never silently ignore a Security-category finding of `high` severity or
     above. "Codacy is advisory" covers style; it does not cover those. Triage
     them explicitly and record the outcome in the PR.
   - Note that Codacy results for a pull request are published against
     `refs/pull/<n>/merge`, not `refs/pull/<n>/head`.
1. Agents used should be explicitly acknowledged in PR descriptions and
   `AUTHORS.rst`, but the submitting user retains responsibility for the content
   submitted.
1. Submit.

## Reporting

Before opening a pull request, write Part 1 of your report for the unit to
`reports/<N>-NN-<slug>.md`, named to match its prompt (copy
`reports/TEMPLATE.md`), and commit it on the same branch. A pull request opened
without its committed report is incomplete and will not be reviewed. State in
the report which checks you ran (`tox -e check`, `tox -e py314-cover`) and their
results, and list any sensitive paths you touched (see
`.claude/reference/local-conventions.md`).
