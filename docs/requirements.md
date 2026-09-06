# Campaign Logger — Requirements

What this project is required to do, and whether it currently does it.

Requirements were never written down as such: they were stated as inline review
comments on pull requests, chiefly [#1] and [#10], and in issues [#2], [#12] and
[#13]. This document collects them and records each one's status against `main`,
verified by reading the merged code rather than by trusting the claim made at
the time.

Status is **Met** (verified in code), **Partial**, **Not met** (verified
absent), or **Unverified** (no objective check applied). Where a row cites a
file and line, that is the evidence. Rows backed by a test are more durable than
rows backed by prose — see [#52] for the guidance on converting them.

## 1. Logger API client

| #   | Requirement                                                                       | Status                                                                                                                                                       |
| --- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1.1 | Authenticate with `api-client` / `api-secret` headers                             | **Met** — `api.py:151`                                                                                                                                       |
| 1.2 | No intermediate `JsonApi*` model classes; JSON stays a dict until the final class | **Met**                                                                                                                                                      |
| 1.3 | Objects expose `save()` rather than `update(raw_text=...)`                        | **Met** — `Campaign`, `Log`, `LogEntry`, `CampaignEntry`, `GeneratorModel`. The client layer keeps `update_*(id, raw_text)` as its transport                 |
| 1.4 | Look up a campaign by title                                                       | **Not met** — no `get_campaign_by_title`; id only. [#45](https://github.com/Ciemaar/campaign_logger/issues/45)                                               |
| 1.5 | Model every attribute the swagger defines, on every object                        | **Not met** — `CampaignEntry` carries `id`, `type`, `raw_text`, `tag_value`, `campaign_id` only. [#44](https://github.com/Ciemaar/campaign_logger/issues/44) |
| 1.6 | Refer to the main application API as the *logger api* throughout                  | **Unverified** — `LoggerClient` is named correctly; prose not audited                                                                                        |
| 1.7 | Credentials must not follow a cross-host redirect                                 | **Met** — `LoggerSession`, `api.py:137`, tested                                                                                                              |

## 2. Generator API client

| #   | Requirement                                               | Status                                         |
| --- | --------------------------------------------------------- | ---------------------------------------------- |
| 2.1 | Authenticate with `Authorization: Bearer`                 | **Met** — `api.py:27`                          |
| 2.2 | Unwrap list responses from the `generators` key           | **Met** — `api.py:43`                          |
| 2.3 | Unwrap single-generator responses from the same key       | **Met** — `api.py:53`, `71`, `84`              |
| 2.4 | Look up a generator by name                               | **Met** — `get_generator_by_name`, `api.py:57` |
| 2.5 | Model class named `GeneratorModel`                        | **Met**                                        |
| 2.6 | Object-oriented API: `generate()`, `validate()`, `save()` | **Met** — plus `delete()`, `models.py:52-69`   |

## 3. Command line interface

| #   | Requirement                                                               | Status                                                                                                                                                                |
| --- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 3.1 | Listings show titles, falling back to the first line of text              | **Partial** — `cli.py:388-395`; items with neither title nor text are dropped from the listing rather than shown by id                                                |
| 3.2 | Pages and entries filter by log or campaign by default                    | **Met** — `CL_DEFAULT_LOG_ID` / `CL_DEFAULT_CAMPAIGN_ID`                                                                                                              |
| 3.3 | Getting a page or entry returns its text, richly formatted where possible | **Met** — `--raw` for the fallback                                                                                                                                    |
| 3.4 | Generators addressable by title                                           | **Met** — `cli.py:85`, `156`, `187`                                                                                                                                   |
| 3.5 | Explained failure when authentication is absent                           | **Met** — `cli.py:55`, `206`                                                                                                                                          |
| 3.6 | Config file for secrets                                                   | **Met** — `~/.campaign_logger.json`. No permission enforcement, and secrets are copied into `os.environ`: [#40](https://github.com/Ciemaar/campaign_logger/issues/40) |

## 4. MCP server

| #   | Requirement                              | Status                                                |
| --- | ---------------------------------------- | ----------------------------------------------------- |
| 4.1 | MCP server for access to Campaign Logger | **In progress** — PR #27                              |
| 4.2 | Read-only and read-write modes           | **In progress** — `campaign-logger mcp [--read-only]` |
| 4.3 | Usable by Gemini Spark                   | **Unverified**                                        |

## 5. Player logs

| #   | Requirement                                            | Status                   |
| --- | ------------------------------------------------------ | ------------------------ |
| 5.1 | Player Logs and Player Log Entries, in library and CLI | **In progress** — PR #30 |

## 6. Testing

| #   | Requirement                                 | Status                                                                                                    |
| --- | ------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| 6.1 | 95% coverage gate                           | **Met** — `tox.ini`, `pyproject.toml:75`                                                                  |
| 6.2 | Coverage must increase with every PR        | **Not met** — a fixed floor is not a ratchet. [#46](https://github.com/Ciemaar/campaign_logger/issues/46) |
| 6.3 | Test secrets generated, not hardcoded       | **Partial** — literals remain in `tests/test_e2e.py:99`, `:115` and `tests/test_logger_api.py:11`         |
| 6.4 | Tests live outside `src/`                   | **Met**                                                                                                   |
| 6.5 | `conftest.py` mechanisms documented         | **Met**                                                                                                   |
| 6.6 | End-to-end tests skipped unless `--run-e2e` | **Met**                                                                                                   |
| 6.7 | No coverage pragmas on authentication code  | **Met** — all four removed with [#39](https://github.com/Ciemaar/campaign_logger/issues/39)               |

## 7. Build, packaging and release

| #   | Requirement                                                     | Status                                                                                                                                                                                    |
| --- | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 7.1 | Patch version increases with every PR                           | **Not met** — `.bumpversion.cfg` says `0.0.0` where the package says `0.0.1`, and targets a `setup.py` that no longer exists. [#48](https://github.com/Ciemaar/campaign_logger/issues/48) |
| 7.2 | `pyproject.toml` is the single source of configuration          | **Partial** — `setup.cfg` is retained because `ci/bootstrap.py` reads its `[matrix]` section                                                                                              |
| 7.3 | Minimum Python 3.11                                             | **Met** — matrix is 3.11–3.14                                                                                                                                                             |
| 7.4 | CI on the newest available Ubuntu                               | **Met**                                                                                                                                                                                   |
| 7.5 | ReadTheDocs published, with setup documented                    | **Not met** — `.readthedocs.yml` is valid but the project was never imported. [#47](https://github.com/Ciemaar/campaign_logger/issues/47)                                                 |
| 7.6 | `tox.ini` and the build workflow generated from `ci/templates/` | **Met** — enforced by the `bootstrap drift` CI job                                                                                                                                        |

## 8. Process

| #   | Requirement                                                               | Status                                   |
| --- | ------------------------------------------------------------------------- | ---------------------------------------- |
| 8.1 | Agents monitor GitHub test results and address failures                   | **Met** as policy — `AGENTS.md`          |
| 8.2 | Codacy findings are advisory, except Security findings at `high` or above | **Met** — `AGENTS.md`                    |
| 8.3 | Agents acknowledged in PRs; the submitting user is responsible            | **Met** — `AUTHORS.rst`                  |
| 8.4 | pre-commit mandatory, with manual fallback documented                     | **Met** — `CONTRIBUTING.rst`             |
| 8.5 | Contributors list crediting agents and tooling                            | **Met** — `AUTHORS.rst`                  |
| 8.6 | Markdown formatter, not only rst                                          | **Met** — `mdformat` with `mdformat-gfm` |

## Open gaps

Everything above marked **Not met** or **Partial**, with its issue:

| Requirement                     | Issue                                                       |
| ------------------------------- | ----------------------------------------------------------- |
| 1.4 campaign lookup by title    | [#45](https://github.com/Ciemaar/campaign_logger/issues/45) |
| 1.5 swagger attribute coverage  | [#44](https://github.com/Ciemaar/campaign_logger/issues/44) |
| 3.6 config file secret handling | [#40](https://github.com/Ciemaar/campaign_logger/issues/40) |
| 6.2 coverage ratchet            | [#46](https://github.com/Ciemaar/campaign_logger/issues/46) |
| 7.1 version bump enforcement    | [#48](https://github.com/Ciemaar/campaign_logger/issues/48) |
| 7.5 ReadTheDocs                 | [#47](https://github.com/Ciemaar/campaign_logger/issues/47) |

## Keeping this current

A status column depends on someone rechecking it. A test does not. Where a row
can be expressed as an assertion, write the assertion and cite the test instead
of a line number — [#52] carries the guidance and the list of directly
convertible rows.

[#1]: https://github.com/Ciemaar/campaign_logger/pull/1
[#10]: https://github.com/Ciemaar/campaign_logger/pull/10
[#12]: https://github.com/Ciemaar/campaign_logger/issues/12
[#13]: https://github.com/Ciemaar/campaign_logger/issues/13
[#2]: https://github.com/Ciemaar/campaign_logger/issues/2
[#52]: https://github.com/Ciemaar/campaign_logger/issues/52
