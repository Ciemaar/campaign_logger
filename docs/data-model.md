# The Campaign Logger data model

For anyone consuming this client — or the API behind it — from another system.
The other documents here are about *building* the client; this one is about what
the data actually is.

Authoritative field list: `https://logger.campaign-logger.com/swagger/v3/swagger.json`,
public and unauthenticated. Where this document and the swagger disagree about a
field name, the swagger is right about *names* and this document is right about
*what crosses the wire* — see [Wire format](#wire-format), which is the one place
they genuinely differ.

## Resource types

Six, and no others:

| Type | What it is |
| --- | --- |
| `campaigns` | A campaign. The top-level container. |
| `logs` | A log within a campaign — usually a session or a thread. |
| `log-entries` | One entry in a log. The actual play text. |
| `campaign-entries` | A **page**: a wiki-like document attached to a campaign. |
| `player-logs` | A log owned by a player rather than the GM. |
| `player-log-entries` | One entry in a player log. |

**There is no entity, NPC, location, item or timeline type.** If you are looking
for those, you want campaign entries — see below.

## Pages are how everything that isn't play text is modelled

A campaign entry carries a `tag_symbol` and a `tag_value`. The symbol says what
kind of thing the page describes; the value is its name. So a page with
`tag_symbol="@"` and `tag_value="Lillian Robin"` *is* the NPC record.

| Symbol | Category | Short name |
| --- | --- | --- |
| `@` | Cast of Characters - People | `people` |
| `^` | Organizations | `organizations` |
| `#` | Gazetteer - Locations | `locations` |
| `$` | Money | `money` |
| `!` | Quartermaster - Equipment, Gear, Weapons | `equipment` |
| `%` | Calendar | `calendar` |
| `*` | Loopy Planning - Plot | `plot` |
| `~` | Rules/Spells | `rules` |
| `§` | Sections | `sections` |
| `+` | Pluses | `pluses` |
| `-` | Minuses | `minuses` |
| `&` | Notes | `notes` |

The categories are Campaign Logger's own words. The short names are this
library's, for consumers that would rather match `"locations"` than
`"Gazetteer - Locations"`; `campaign_logger.tags` exposes both as `TAG_TYPES`
and `TAG_NAMES`, plus `tag_name(symbol)`, which returns `None` for a symbol it
does not know rather than raising — the set belongs to Campaign Logger and can
grow.

**There is no server-side filter by tag.** Fetch the campaign's entries and
filter client-side on `tag_symbol`.

Entry text also uses the symbols inline — `@"Lillian Robin"` inside a log entry
is a reference to that person's page. Parsing those references is not something
this client does.

## Public and private text

This is the distinction most likely to matter, and it is not symmetric.

| Resource | Private body | Public body |
| --- | --- | --- |
| `campaign-entries` (pages) | `raw_text` | `raw_public` |
| `log-entries` | `raw_text` | **none** |
| `player-log-entries` | `raw_text` | **none** |

A page can have content in only its public field, in which case `raw_text` comes
back empty. `CampaignEntry.text` handles that: it returns `raw_text`, falling
back to `raw_public`. Read through it rather than reaching for `raw_text`
directly, so the two stored fields keep reporting exactly what the server sent.

**Log entries have no public variant at all.** Their text is the only text there
is. They do carry an `is_shared` flag, which this client does not act on. So if
you surface log text to players, `is_shared` is the signal to filter on and
nothing in this library will do it for you.

## Fields every resource carries

Audit and revision metadata is on all six:

| Field | Type | Note |
| --- | --- | --- |
| `id` | `str` | 32 lowercase hex |
| `created_on`, `updated_on` | `datetime \| None` | |
| `deleted_on` | `datetime \| None` | `""` from the server becomes `None` |
| `is_deleted` | `bool` | delete is **soft** |
| `revision`, `previous_revision` | `str \| None` | server-assigned; the API keeps full history |
| `string_id`, `user_id` | `str \| None` | |

Then per type: `title`/`description` on campaigns and logs; `raw_text` and the
tag fields on entries; `image_url` and `is_pinned` on logs; `raw_prefix`,
`raw_suffix`, `ordering` and `is_shared` on log entries; `raw_public`,
`raw_summary`, `labels`, `tag_symbol`, `tag_value` on pages.

Nullability follows the API: almost everything is optional, including `title`.

## Wire format

The wire is **JSON:API with kebab-case members**:

```
GET /campaigns/{id}
→ {"data": {"id": "…", "type": "campaigns",
            "attributes": {"created-on": "…", "image-url": "…", "user-id": "…"}}}
```

The swagger describes flat camelCase objects (`createdOn`, `rawText`) under
`application/json` and never mentions `vnd.api+json`. That appears to be
generated from the internal DTOs without the JSON:API serialisation layer. Only
kebab-case crosses the wire, in **both** directions — an unknown attribute on a
write is accepted with `201` and **silently discarded**, which is how this
client once created log entries with no text. The models map snake_case fields
to kebab-case aliases automatically.

The `Accept` header is not honoured; every response is
`application/vnd.api+json` regardless.

## Relationships

Parent links come from the JSON:API `relationships` block, not from an
attribute — `logs` payloads carry no `campaign-id` attribute at all.

**One inconsistency to design around:** a log entry's `log` relationship
includes its `data` linkage, so you can read the parent id straight off the
entry. A **player** log entry's `player-log` relationship carries `meta` and
`links` but **no `data`**, so its parent cannot be resolved from the entry.
`?include=player-log` works. This is why `PlayerLog.get_entries()` currently
returns nothing.

## Things that will bite a consumer

- **Listings can be incomplete.** `get_log_entries(log_id)` and
  `get_campaign_entries(campaign_id)` fetch *every* object of that type in the
  account and filter client-side, and `_get` does not follow pagination. On a
  large account you get a partial set with no error. Treat any listing as
  possibly-partial and surface the gap rather than swallowing it. The server
  returns `meta.total-records`, so truncation is detectable: compare it to what
  you received.
- **Soft delete is not exposed.** Objects can be deleted and restored
  server-side (`cl:deleted`, `cl:undelete`), and full revision history exists
  (`cl:revisions`, `cl:revision-tree`) — about thirty endpoints in all. None are
  in this client yet, so a deleted object simply vanishes from its listing.
- **Player logs are second-class here.** The client models them, the CLI covers
  them, the MCP server does not expose them at all, and their parent id cannot
  be read back.
- **Ids are opaque.** 32 lowercase hex, confirmed across two accounts. Useful
  for telling an id from a name without a round trip, but do not assume more
  than that.

## Getting at it

- **Python**: `LoggerClient` in `campaign_logger.api`; models in
  `campaign_logger.models`; tag helpers in `campaign_logger.tags`.
- **CLI**: `campaign-logger logger …`, and `campaign-logger logger campaign
  rag-export <id>` to dump a campaign to flat text.
- **MCP**: `campaign-logger mcp`, read-only by default. See
  [mcp-server.md](mcp-server.md).

Auth is an `api-client` / `api-secret` header pair, from
`~/.campaign_logger.json` or the `CL_LOGGER_CLIENT_ID` / `CL_LOGGER_CLIENT_SECRET`
environment variables.
