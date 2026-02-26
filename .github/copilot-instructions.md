# GitHub Copilot Instructions

This repository uses **Ruff** for linting/formatting and **Pyright** for type checking.
All Python code must be compatible with Python 3.9 through 3.14.

## Key Directives

- **Linting & Formatting:** Always adhere to `ruff` rules. Line length is 140.
- **Type Checking:** Use strict type hints compatible with `pyright`.
- **Testing:** Use `pytest` with `tox`. Do not use `unittest` unless necessary.
- **Imports:** Sort imports using `ruff` (isort rules).
- **CLI:** Use `click` for command-line interfaces.
- **Models:** Use `pydantic` v2 for data models.

## Project Structure

- `src/campaign_logger/`: Source code.
- `tests/`: Tests (mirrors source structure).
- `tox.ini`: Testing configuration.
- `pyproject.toml`: Tool configuration.

For more details on configuring custom instructions, see:
https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions?tool=jetbrains
