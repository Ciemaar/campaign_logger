# Campaign Logger — Requirements of Record

Reconstructed from GitHub issues and pull requests, 2026-02-25 → 2026-09-03.

## Why this document exists

Essentially all of this codebase was written by `google-labs-jules[bot]`, driven
by @Ciemaar. There was never a requirements document — requirements were stated
as **inline review comments**, mostly on
**[PR #1](https://github.com/Ciemaar/campaign_logger/pull/1)** and
**[PR #10](https://github.com/Ciemaar/campaign_logger/pull/10)**, neither of
which was merged. Both were superseded through a chain of re-rolls (#1 → #5 → #7
→ #9 → #10 → **#11**), and #11 squashed everything in at once.

Because the requirements lived in closed, unmerged PR threads, each was answered
by the agent with a claim of completion that **was never verified against the
code that actually landed**. This document restates each requirement, cites its
source, and records its verified status against `main` @ `0809ece`.

Every comment was also submitted as its own review — 20 separate review
submissions on PR #1, 12 on PR #10, one comment each. The agent therefore never
saw the feedback as a set, which is the most likely cause of the narrow and
dropped answers recorded below.

Status key: **Met** — verified in code · **Partial** — some of it · **Not met**
— verified absent · **Unverified** — no objective check applied.

## 1. API client — Logger API

Source: PR #1 inline review, 2026-03-11.

| #   | Requirement                                                                                                                                                           | Source                                                  | Status                                                                                                                                                                                                                                                                                                        |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1.1 | Logger API authenticates with `api-client` and `api-secret` **headers** (not Bearer).                                                                                 | [#1](https://github.com/Ciemaar/campaign_logger/pull/1) | **Met** — `api.py:151`                                                                                                                                                                                                                                                                                        |
| 1.2 | Drop the `JsonApi*` intermediate model classes; JSON stays a plain dict until it is passed into the final class.                                                      | #1                                                      | **Met** — no such classes in `models.py`                                                                                                                                                                                                                                                                      |
| 1.3 | Replace `update(raw_text=...)`-style signatures with a `save()` method that sends `self.raw_text` and the rest of the object's state.                                 | #1                                                      | **Met** at the model layer — `save()` on `Campaign`, `Log`, `LogEntry`, `CampaignEntry`, `GeneratorModel`. The client layer still exposes `update_*(id, raw_text)` as the transport.                                                                                                                          |
| 1.4 | Offer a way to **get a campaign by title**.                                                                                                                           | #1                                                      | **Not met** — no `get_campaign_by_title`; lookup is by id only. See [#45](https://github.com/Ciemaar/campaign_logger/issues/45).                                                                                                                                                                              |
| 1.5 | Campaign entries have many more attributes than are modelled — *"are all attributes included in the swagger document being represented on all objects? Can they be?"* | #1                                                      | **Not met.** The agent replied that `title`, `description`, `html_text` and `tag_ids` had been bound. Current `CampaignEntry` carries only `id`, `type`, `raw_text`, `tag_value`, `campaign_id`. The underlying question was never answered. See [#44](https://github.com/Ciemaar/campaign_logger/issues/44). |
| 1.6 | The main application API is to be called the **logger api** consistently.                                                                                             | #1 (`docs/usage.rst`)                                   | **Unverified** — `LoggerClient` is named correctly; prose across README/docs not audited.                                                                                                                                                                                                                     |

## 2. API client — Generator API

Source: PR #1 inline review, 2026-03-11.

| #   | Requirement                                                                                                | Source                           | Status                                                                                              |
| --- | ---------------------------------------------------------------------------------------------------------- | -------------------------------- | --------------------------------------------------------------------------------------------------- |
| 2.1 | Generator API authenticates with `Authorization: Bearer <token>`.                                          | #1                               | **Met** — `api.py:27`                                                                               |
| 2.2 | Generator list responses nest the list under a `generators` key, not at the response root. Adjust parsing. | #1 (with captured live response) | **Met** — `api.py:43`                                                                               |
| 2.3 | Single-generator responses are **also** nested under `generators`. Confirm against the swagger.            | #1                               | **Met** in code (`api.py:53`, `71`, `84`) — but the swagger confirmation asked for was never given. |
| 2.4 | Add a method to get a generator **by name**, resolving via the list if needed.                             | #1                               | **Met** — `get_generator_by_name`, `api.py:57`                                                      |
| 2.5 | Name the model `GeneratorModel`.                                                                           | #1                               | **Met**                                                                                             |
| 2.6 | Generators get an object-oriented API like the logger objects: `generate()`, `validate()`, `save()`.       | #1                               | **Met** — plus `delete()`, `models.py:52-69`                                                        |

## 3. CLI usability

Source: issues **#12** and **#13** (byte-identical duplicates), implemented by
PR #21.

| #   | Requirement                                                                               | Status                                                                                                                                                                    |
| --- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 3.1 | Entry and page listings show titles; for untitled items, show the first line.             | **Partial** — implemented at `cli.py:388-395`, but items with neither a title nor text are silently `continue`d and vanish from the listing rather than showing their id. |
| 3.2 | Pages and entries filter by log or campaign **by default**.                               | **Met** — `CL_DEFAULT_LOG_ID` / `CL_DEFAULT_CAMPAIGN_ID`, `cli.py:379`, `cli.py:479`                                                                                      |
| 3.3 | Getting a page or entry returns its text, richly formatted where possible, raw where not. | **Met** — `--raw` flag on `entry get` / `page get`                                                                                                                        |
| 3.4 | Generators are requestable **by title**.                                                  | **Met** — `cli.py:85`, `156`, `187`                                                                                                                                       |
| 3.5 | Graceful, explained failure when no authentication is provided.                           | **Met** — `cli.py:55-56`, `206-207`                                                                                                                                       |
| 3.6 | Support a config file for secrets.                                                        | **Met** — `~/.campaign_logger.json` via `load_config()`. See caveats below.                                                                                               |

**Caveats on 3.6**, not covered by the original requirement: the config file's
permissions are never checked or enforced (no `0600`), and its secrets are
copied into `os.environ`, where any subprocess inherits them. Tracked as
[#40](https://github.com/Ciemaar/campaign_logger/issues/40).

## 4. MCP server

Source: issue **[#2](https://github.com/Ciemaar/campaign_logger/issues/2)** —
open.

| #   | Requirement                                          | Status                                                |
| --- | ---------------------------------------------------- | ----------------------------------------------------- |
| 4.1 | Provide an MCP server for access to Campaign Logger. | **In progress** — PR #27, open                        |
| 4.2 | Support both **read-only** and read-write modes.     | PR #27 proposes `campaign-logger mcp [--read-only]`   |
| 4.3 | Usable by Gemini Spark if possible.                  | **Unverified** — no evidence of testing against Spark |

## 5. Player logs

Source: PR **#30** — open. Derived from the Campaign Logger swagger rather than
from a stated requirement.

| #   | Requirement                                                                                                          | Status                         |
| --- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| 5.1 | Support Player Logs and Player Log Entries so standard and player logs are both feature-complete in library and CLI. | **In progress** — PR #30, open |

## 6. Testing and coverage

| #   | Requirement                                                                      | Source                                                    | Status                                                                                                                                               |
| --- | -------------------------------------------------------------------------------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 6.1 | Coverage gate of **95%**.                                                        | #1, #5                                                    | **Met** — `--cov-fail-under=95` in `tox.ini`, `fail_under = 95` in `pyproject.toml`                                                                  |
| 6.2 | Coverage must **increase with every PR**; it may not be removed.                 | [#10](https://github.com/Ciemaar/campaign_logger/pull/10) | **Not met.** A fixed floor is not a ratchet — nothing detects a decrease above 95%. See [#46](https://github.com/Ciemaar/campaign_logger/issues/46). |
| 6.3 | Test secrets must be randomly generated, not hardcoded.                          | #1 (twice)                                                | **Partial** — `secrets.token_hex(16)` was adopted, but literals remain at `tests/test_e2e.py:99`, `:115` and `tests/test_logger_api.py:11`.          |
| 6.4 | Tests do not live under `src/campaign_logger/tests/`.                            | #1                                                        | **Met** — directory removed                                                                                                                          |
| 6.5 | `conftest.py` mechanisms must be documented for developers unfamiliar with them. | #10                                                       | **Met** — docstrings present, after having to ask twice                                                                                              |
| 6.6 | End-to-end tests are skipped unless `--run-e2e` is passed.                       | #10                                                       | **Met** — `tests/conftest.py`                                                                                                                        |

**Gap not covered by any requirement:** the four `# pragma: no cover` directives
in `api.py` sit on the authentication-header assignments, so the
security-critical lines of both clients are excluded from the 95% gate. Tracked
as [#41](https://github.com/Ciemaar/campaign_logger/issues/41).

## 7. Build, packaging and release

| #   | Requirement                                                          | Source                                                                                | Status                                                                                                                                                                                                                                                                                            |
| --- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 7.1 | At least the **patch version must increase with every PR**.          | #1                                                                                    | **Not met, and mechanically broken.** `.bumpversion.cfg` says `current_version = 0.0.0` while `__init__.py`, `pyproject.toml` and `docs/conf.py` say `0.0.1`, and the config still points at `setup.py`, which no longer exists. See [#48](https://github.com/Ciemaar/campaign_logger/issues/48). |
| 7.2 | `pyproject.toml` is the single source of project configuration.      | #10                                                                                   | **Partial by design.** `setup.cfg` is retained solely because `ci/bootstrap.py` parses it for the tox matrix — a documented and reasonable exception.                                                                                                                                             |
| 7.3 | Minimum Python is **3.11**.                                          | #1 — accepted after the py3.9/3.10 macOS `libintl.8.dylib` CI failure was never fixed | **Met** — `target-version = "py311"`, matrix is 3.11–3.14                                                                                                                                                                                                                                         |
| 7.4 | Run CI on the newest available Ubuntu.                               | #4                                                                                    | **Met**                                                                                                                                                                                                                                                                                           |
| 7.5 | ReadTheDocs must be set up, with a file documenting the setup steps. | #10                                                                                   | **Not met.** `.readthedocs.yml` is valid, but the project was never imported into RTD and no setup-instructions file exists. See [#47](https://github.com/Ciemaar/campaign_logger/issues/47).                                                                                                     |

## 8. Process and contribution

Source: PR #10 inline review, 2026-07-16. These were requested as additions to
`AGENTS.md` and `CONTRIBUTING.rst`.

| #   | Requirement                                                                                                                                                       | Status                                                                                                                                                                      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 8.1 | Agents must monitor GitHub test results and address any failure.                                                                                                  | **Unverified** — currently violated in practice: `Codacy Security Scan` has been failing since 2026-09-01. See [#35](https://github.com/Ciemaar/campaign_logger/issues/35). |
| 8.2 | **Codacy findings are advisory** and are exempt from 8.1.                                                                                                         | **Met** as written — but it was applied to unread `high`-severity Security findings on #21. See [#37](https://github.com/Ciemaar/campaign_logger/issues/37).                |
| 8.3 | Agents used must be acknowledged in PRs; the **submitting user is responsible** for the content submitted.                                                        | **Met** — every agent PR carries a Jules attribution footer; `AUTHORS.rst` has an AI Agents section.                                                                        |
| 8.4 | pre-commit is mandatory for agents and all developers, with documented setup **and** instructions for running the checks manually when pre-commit is unavailable. | **Met** — `.pre-commit-config.yaml` and instructions in `CONTRIBUTING.rst`.                                                                                                 |
| 8.5 | Maintain a contributors list following best practice for crediting agents and tooling.                                                                            | **Met** — `AUTHORS.rst`                                                                                                                                                     |
| 8.6 | Markdown must have a formatter, not only rst.                                                                                                                     | **Met** — `mdformat`. Note it needed `mdformat-gfm` added before it could handle tables without destroying them.                                                            |

## Requirements that were asked for and never answered

Open questions from review threads that were closed without resolution. All are
now filed.

| Req | Question                                                                                                                                                                                  | Issue                                                       |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| 1.5 | *"are all attributes included in the swagger document being represented on all objects? Can they be?"* Answered narrowly with four field names, three of which are not in the code today. | [#44](https://github.com/Ciemaar/campaign_logger/issues/44) |
| 1.4 | Get campaign by title — requested, acknowledged, never implemented.                                                                                                                       | [#45](https://github.com/Ciemaar/campaign_logger/issues/45) |
| 6.2 | Coverage ratchet — a fixed floor was delivered where a ratchet was asked for.                                                                                                             | [#46](https://github.com/Ciemaar/campaign_logger/issues/46) |
| 7.5 | ReadTheDocs — never actually connected; the README URL is a placeholder.                                                                                                                  | [#47](https://github.com/Ciemaar/campaign_logger/issues/47) |
| 7.1 | Version bump per PR — unenforced, and `.bumpversion.cfg` is broken.                                                                                                                       | [#48](https://github.com/Ciemaar/campaign_logger/issues/48) |
| —   | Duplicate records: issues #12/#13 identical; PR #25 duplicates merged PR #3.                                                                                                              | [#49](https://github.com/Ciemaar/campaign_logger/issues/49) |

## Security findings

Not requirements — defects and gaps found while verifying the above.

| Finding                                                                                               | Severity | Issue                                                       |
| ----------------------------------------------------------------------------------------------------- | -------- | ----------------------------------------------------------- |
| Logger API `api-client`/`api-secret` leak to third-party hosts on cross-host redirect (PoC confirmed) | high     | [#39](https://github.com/Ciemaar/campaign_logger/issues/39) |
| Config file secrets: no `0600` enforcement, copied into `os.environ`                                  | medium   | [#40](https://github.com/Ciemaar/campaign_logger/issues/40) |
| Auth code excluded from the 95% gate by `# pragma: no cover`                                          | medium   | [#41](https://github.com/Ciemaar/campaign_logger/issues/41) |
| Secrets accepted as CLI flags — shell history, process table                                          | low      | [#42](https://github.com/Ciemaar/campaign_logger/issues/42) |
| No HTTP timeouts anywhere in the clients                                                              | low      | [#43](https://github.com/Ciemaar/campaign_logger/issues/43) |
| Workflow `GITHUB_TOKEN` permissions unset                                                             | medium   | [#34](https://github.com/Ciemaar/campaign_logger/issues/34) |
| Codacy SARIF upload failing — no scan results since 2026-09-01                                        | —        | [#35](https://github.com/Ciemaar/campaign_logger/issues/35) |
| Jinja2 autoescape (B701) in `ci/bootstrap.py`                                                         | low      | [#36](https://github.com/Ciemaar/campaign_logger/issues/36) |
| Codacy findings merged unreviewed on #11 and #21                                                      | —        | [#37](https://github.com/Ciemaar/campaign_logger/issues/37) |
| 1288 open code-scanning alerts drowning real findings                                                 | —        | [#38](https://github.com/Ciemaar/campaign_logger/issues/38) |

## Sources

Full JSON export of every closed issue and PR, with comments, reviews and inline
review comments, was taken on 2026-09-03 via `gh`. Primary sources: PR #1 (20
inline comments), PR #10 (12 inline comments), issues #2, #12, #13.
