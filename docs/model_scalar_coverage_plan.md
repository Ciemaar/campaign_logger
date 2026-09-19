# Plan: full scalar coverage for the resource models (#44)

Bring `Campaign`, `Log`, `LogEntry`, `CampaignEntry`, `PlayerLog` and
`PlayerLogEntry` to every scalar attribute the API defines, typed to match the
API, and enforce the coverage with a test so the gap cannot silently reopen.

Source of truth: the live swagger (identical on staging and production), plus
the observed wire format captured in `docs/live_testing_evidence.md`.

## Decisions (settled)

- **Casing: kebab-case only.** The wire sends kebab-case (`created-on`,
  `raw-text`, `user-id`); the swagger schema names are camelCase but that is not
  what crosses the wire. We support only what the API sends. A single
  `alias_generator` that maps a snake_case field to its kebab-case form
  (`raw_text` → `raw-text`) replaces every hand-written
  `attrs.get("rawText", attrs.get("raw-text"))` hedge. The mocks are corrected
  to kebab-case to match reality.

  Checked against the Pydantic documentation rather than assumed: an
  `alias_generator` in `model_config` is what Pydantic recommends for applying
  a naming convention across every field, in preference to per-field aliases —
  *"You can use the `alias_generator` parameter of `Config` to specify a
  callable ... that will generate aliases for all fields in a model."* A plain
  callable applies the same transform to validation and serialisation, which is
  what we want since the wire format is symmetric; `AliasGenerator` exists for
  the asymmetric case and we do not need it. `populate_by_name` remains valid in
  Pydantic 2.13 (verified: no deprecation warning) and lets the field names
  still be used directly, which the tests rely on. Serialisation defaults to
  field names, so `model_dump()` and the MCP server's `model_dump_json()` are
  unaffected; `by_alias=True` produces the kebab wire form when needed.
- **Types match API limits.** Nullable attributes become `X | None`; timestamps
  become `datetime`. `is-deleted` / `is-pinned` / `is-shared` are `bool`.
- **A `Player` model** is added for `joined-players`.
- **Sequencing:** Campaign + Log first as the pattern (verified against a live
  staging read), then fan out to the entry and player-log types.

## Field inventory (from the swagger)

Common to all six, so they live on `BaseEntity`:

| field | wire key | type |
| --- | --- | --- |
| `created_on` | `created-on` | `datetime \| None` |
| `updated_on` | `updated-on` | `datetime \| None` |
| `deleted_on` | `deleted-on` | `datetime \| None` (empty string → None) |
| `is_deleted` | `is-deleted` | `bool` |
| `revision` | `revision` | `str \| None` |
| `previous_revision` | `previous-revision` | `str \| None` |
| `string_id` | `string-id` | `str \| None` |
| `user_id` | `user-id` | `str \| None` |

Per-resource additions:

| resource | added fields |
| --- | --- |
| `Campaign` | `image_url`, `invited_players: list[str]`, `joined_players: list[Player]` |
| `Log` | `image_url`, `is_pinned` |
| `PlayerLog` | `image_url`, `is_pinned` |
| `LogEntry` | `is_shared`, `ordering`, `raw_prefix`, `raw_suffix` |
| `PlayerLogEntry` | `is_shared`, `ordering`, `raw_prefix`, `raw_suffix` |
| `CampaignEntry` | `raw_public`, `raw_summary`, `tag_symbol`, `tag_value_case_insensitive`, `labels: list[str]` |

`Player`: `email_address`, `email_address_case_insensitive`, `joined_campaigns: list[str]`.

Existing fields also re-typed to the API's nullability: `title`, `description`,
`raw_text`, `tag_value`, `campaign_id`, `log_id` become `X | None`. `id`/`type`
stay required (always present at the JSON:API resource level).

## Work breakdown

1. **`models.py`** — `model_config` on `BaseEntity` (`alias_generator` snake→kebab,
   `populate_by_name=True`, `extra="ignore"`); a datetime `before` validator that
   maps `""`/absent to `None`; the common fields on `BaseEntity`; the `Player`
   model; per-resource fields; nullability corrections.
2. **`api.py`** — each `_parse_*` becomes `Model.model_validate({**attrs, "id":…,
   "type":…})`, keeping the relationship fallback for `campaign_id`/`log_id`
   (the real `logs` payload has no `campaign-id` attribute, so this stays
   load-bearing).
3. **Mocks & fixtures** — correct the camelCase mocks in `test_e2e.py` and
   `test_logger_api.py` to kebab-case; the `tests/fixtures/*_kebab.json` already
   match reality and grow assertions for the new fields.
4. **Coverage test** — a test that reads the swagger scalar set for each resource
   and asserts the model defines a field for each, failing if a scalar is
   unmodelled. This encodes #44 as CI rather than prose.
5. **Docs** — flip the #44 row to met/enforced.

## Sequencing

- **Phase 1:** `BaseEntity` config + common fields + `Player`, then `Campaign`
  and `Log` (+ their parsers, mocks, tests). Verify field population against a
  live staging read.
- **Phase 2:** `LogEntry`, `CampaignEntry`, `PlayerLog`, `PlayerLogEntry`.
- **Phase 3:** the swagger-coverage test and docs.

## Risks

- `title`/`description` becoming `str | None` changes CLI output from `""` to
  `None` for absent values; guard the display sites in `cli.py` if needed.
- The 95% coverage gate — new fields need assertions to stay above the floor.
- Not in scope: the `cl:` revision/undelete/deleted endpoints (30 of them) are a
  separate API-surface addition, tracked separately.
