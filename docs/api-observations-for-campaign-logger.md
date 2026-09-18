# Observations on the Campaign Logger v3 API

Notes for the Campaign Logger developers, gathered while building an open-source
Python client. Everything below was observed against
`logger-staging.campaign-logger.com` in September 2026, using a normal account
credential, and compared against `/swagger/v3/swagger.json` from the same host
(byte-identical to the production document).

These are offered as observations rather than complaints — the API has been
pleasant to work against, and the soft-delete and revision endpoints in
particular are unusually thoughtful. The notes are simply the places where the
published description and the observed behaviour differ, in case they are
useful. Every item includes what we did, so anything that is actually our
misunderstanding should be easy to spot and correct.

## 1. The swagger describes a different representation than the API serves

The swagger describes each endpoint as taking and returning a flat object with
**camelCase** properties (`campaignId`, `rawText`, `createdOn`) under
`application/json`.

What the server actually returns is a **JSON:API document** — a `data` envelope
with `attributes` and `relationships` — using **kebab-case** member names:

```
GET /campaigns/{id}
→ 200, Content-Type: application/vnd.api+json
  {"data": {"id": "...", "type": "campaigns",
            "attributes": {"created-on": "...", "image-url": "...",
                           "invited-players": null, "user-id": "...", ...}}}
```

The string `vnd.api+json` does not appear anywhere in the swagger document.

Our guess is that the document is generated from the internal DTOs without the
JSON:API serialisation layer in the pipeline, so it reflects the C# property
names rather than the wire format. If that is right, a note in the
documentation to that effect would save client authors a fair amount of
detective work — we spent some time assuming the two casings were alternative
representations before concluding that only kebab-case ever crosses the wire.

## 2. `Accept` does not appear to be honoured

We tried `application/vnd.api+json`, `application/json` and `*/*` on the same
resource. All three returned an identical JSON:API response with
`Content-Type: application/vnd.api+json`.

This is entirely reasonable if JSON:API is the only representation. It is worth
stating explicitly, though, because the swagger's `application/json` content
types suggest a plain representation is available, and a client may be built
expecting to negotiate one.

## 3. Unknown attributes on write are accepted and silently discarded

This is the item with the most potential to bite, so we have described it in
detail.

Posting a log entry with the attribute spelled the way the swagger spells it:

```
POST /log-entries
{"data": {"type": "log-entries",
          "attributes": {"rawText": "some text", "title": "a title"},
          "relationships": {"log": {"data": {"type": "logs", "id": "..."}}}}}
```

returns **201 Created**. The entry is created and correctly attached to its
log — but its `raw-text` is `null`. The body text is gone, with no error and no
warning.

The same request with `raw-text` behaves correctly and round-trips the text.

Two things make this easy to walk into:

- `title` is casing-neutral, so it survives either spelling. A smoke test that
  creates an entry and checks its title will pass while the body is being
  dropped.
- `rawText` is precisely the spelling the swagger schema uses, so a client
  generated or hand-written from the published document will hit this by
  default.

JSON:API permits returning `400 Bad Request` for unknown members, and doing so
here would turn a silent data loss into an obvious, immediately fixable error.
If strictness would be a breaking change for existing clients, even documenting
the kebab-case requirement would help.

## 4. Query parameters are supported but not documented

The swagger lists **no parameters** for the collection endpoints
(`GET /logs`, `/log-entries`, `/campaign-entries`, `/campaigns`,
`/player-log-entries`). In practice several work:

| request | result |
| --- | --- |
| `GET /log-entries?page[size]=1` | 200, one item, `meta.total-records: 551` |
| `GET /log-entries?page[size]=2&page[number]=2` | 200, second page |
| `GET /logs?filter[title]=x` | 200, filtered (0 matches) |

`meta.total-records` on the unparameterised listing is genuinely useful, and
pagination working is reassuring. Documenting these — particularly whether
there is a maximum page size, and what the default is when `page[size]` is
omitted — would let clients size their requests responsibly. We did not find a
cap: `page[size]=1000` against a 551-record collection returned all 551.

## 5. `filter=equals(...)` returns HTTP 500

The expression-style filter syntax appears to be partially wired up:

```
GET /logs?filter=equals(title,'x')
→ 500
  {"errors":[{"title":"IndexOutOfRangeException",
              "detail":"Index was outside the bounds of the array.","status":"500"}]}
```

`GET /logs?filter=equals(campaign-id,'<id>')` fails the same way. The
bracket form (`filter[title]=x`) works, so this looks like an unsupported
syntax reaching code that assumes it has already been parsed. Returning `400`
for a filter expression the server does not support would be friendlier than a
500, and would tell a client author which syntax to use.

## 6. Filtering a collection by its parent id is rejected

Both spellings are refused:

```
GET /logs?filter[campaign-id]=<id>  → 400 "'campaign-id' is not a valid attribute."
GET /logs?filter[campaignId]=<id>   → 400 "'campaignId' is not a valid attribute."
```

We take this to mean relationships are not filterable as attributes, which is
consistent with JSON:API. The related-resource routes (below) do the job well,
so this is not a gap so much as a place where a pointer in the documentation
would help — the error message is accurate but does not suggest the alternative.

## 7. The related-resource routes work well and deserve to be more visible

These are the efficient way to scope a collection, and they behave exactly as
hoped:

```
GET /campaigns/{id}/logs          → only that campaign's logs
GET /logs/{id}/log-entries        → only that log's entries (99, where the
                                    unscoped collection returns 551)
GET /campaigns/{id}/campaign-entries
```

In the swagger they appear only as a generic
`/{resource}/{id}/{relationshipName}`, so there is no way to discover which
relationship names are valid for which type without trying them. Listing the
valid relationship names per resource would make this discoverable — it is a
much better answer than client-side filtering, and we only found it by noticing
the `related` links inside response payloads.

One small note: these routes return no `meta.total-records`, where the
top-level collections do. Not a problem, just an inconsistency we noticed.

## 8. Responses declare no content type in the swagger

The `responses` entries for the collection GETs have an empty `content` object,
so a generated client cannot infer the response media type or schema. Given
item 1, populating these with the JSON:API document shape would be the single
most useful change for anyone generating a client from the document.

## Thank you

None of the above prevented us from building a working client, and the parts
that are not in the document were all discoverable with a little
experimentation. The revision and undelete endpoints in particular
(`cl:revisions`, `cl:revision-tree`, `cl:undelete`) are a genuinely nice piece
of design, and we are glad they are documented.

Happy to provide request/response captures for any of the above, or to re-test
anything against staging if it would be useful.
