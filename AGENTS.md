# Agent Instructions (Jules & Others)

This file contains instructions for AI agents working on this repository.

## Core Constraints

1. **Python Version:** Supports Python 3.11 through 3.14. Do not use features
   newer than 3.11 without fallbacks.
1. **Linting:** The project uses `ruff` for both linting and formatting. Run
   `ruff check .` and `ruff format .`.
1. **Type Checking:** The project uses `pyright`. Run `pyright .` to verify
   types.
1. **Testing:** Use `tox` to run tests across environments. `tox -e py312-cover`
   (or similar) is preferred for fast feedback.
1. **Build System:** Uses `setuptools`. Configuration is in `setup.py` and
   `setup.cfg`.
1. **CI/CD:** Configuration is generated via `ci/bootstrap.py`. If you modify
   `setup.cfg` or `ci/templates/`, run `python ci/bootstrap.py`.

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
1. Verify with `tox -e check` (lint/types) and `tox -e py312-cover` (tests).
1. Submit.
