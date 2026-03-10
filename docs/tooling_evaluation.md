# Tooling Evaluation Notes

Date: March 8, 2026

## Linting and Formatting

- **Ruff** (Currently Used):
  - **Suitability:** Excellent. It replaces Flake8, Isort, Black, Pydocstyle, and Pylint in a single, extremely fast Rust binary. It accurately identifies unused imports, line-length violations, and missing docstrings.
  - **Decision:** **Retain Ruff.** It offers the best performance and unified configuration in `pyproject.toml`.
- **Alternative: Black + Flake8 + Isort:**
  - **Suitability:** Good, but requires maintaining multiple configurations (`.flake8`, `pyproject.toml`, etc.) and running multiple slow python-based tools. We migrated away from a similar setup (`pylama` + `isort`).

## Type Checking

- **Pyright** (Currently Used):
  - **Suitability:** Excellent. It integrates perfectly with VS Code / GitHub Copilot and is incredibly fast. It caught several edge cases around Pydantic model typing during the API client implementation.
  - **Decision:** **Retain Pyright.**
- **Alternative: Mypy:**
  - **Suitability:** Strong industry standard. Tested locally on the codebase: `mypy src/ tests/`. It passed cleanly (after installing `types-requests`). However, Pyright's speed and strictness out of the box make it preferable for this project's current footprint.

## Testing and Matrix Orchestration

- **Tox** (Currently Used):
  - **Suitability:** Excellent. The project uses a complex `ci/bootstrap.py` script to generate massive matrix configurations for Windows, macOS, and Linux across Python 3.9 - 3.14. Tox handles this natively via `tox.ini`.
  - **Decision:** **Retain Tox.**
- **Alternative: Nox:**
  - **Suitability:** Nox uses Python files instead of INI files for configuration, which is elegant. However, migrating the custom Jinja2 template (`ci/templates/tox.ini`) and `bootstrap.py` logic to a `noxfile.py` would require substantial churn with minimal tangible benefit to the CI pipeline runtime.

## Documentation

- **Sphinx** (Currently Used):
  - **Suitability:** Standard for Python projects. Handles `.rst` files well and generates the existing readthedocs output.
  - **Decision:** **Retain Sphinx.**
- **Alternative: MkDocs:**
  - **Suitability:** Excellent for Markdown. Since we use `.rst` for `CHANGELOG.rst`, `AUTHORS.rst`, and `CONTRIBUTING.rst`, moving to MkDocs would require converting all these files to Markdown. Sphinx already works.

## Markdown Formatting

- **mdformat** (Currently Used):
  - **Suitability:** Lightweight, strict CommonMark formatting. Works perfectly as a pre-commit hook and in Tox.
  - **Decision:** **Retain mdformat.**

## Conclusion

The current toolchain (Ruff, Pyright, Tox, Pytest, Sphinx, mdformat) represents the state-of-the-art for a modern Python library. It balances incredible speed (Ruff/Pyright) with deep ecosystem compatibility (Tox/Sphinx). No tool replacements are recommended at this time.
