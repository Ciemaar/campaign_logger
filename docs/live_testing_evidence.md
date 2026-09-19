# Live testing: salvaged evidence

Evidence extracted from the untracked `tests_live/` directory before it was
deleted under Phase 0.4 of the live-server test plan (issue #62). The directory
held hardcoded live credentials and could not be imported against `main`, so it
was removed; this file preserves the only parts worth keeping.

It has since grown past that. Sections marked **ANSWERED** are confirmed
against the live API definition, fetched unauthenticated on 2026-09-16.
Sections marked *original 2022 evidence* are the weaker material the salvage
started from, kept because it is what prompted the checks and because it
records what the server looked like four years ago. Each item is tied to the
open question it bears on in §10 of the plan.

## Q3 — ANSWERED: staging exists, is live, and is current

Confirmed 2026-09-16 by unauthenticated probe. No credentials were sent.

| | production | staging |
| --- | --- | --- |
| host | `logger.campaign-logger.com` | `logger-staging.campaign-logger.com` |
| address | `104.40.250.100` (Azure West Europe) | `51.159.11.132` (Scaleway, Paris) |
| server | Kestrel | Kestrel |
| `GET /campaigns` unauthenticated | 401 | 401 |
| `swagger/v3/swagger.json` | md5 `96f545971b42afca42ce8f3c19d8d29b` | **identical** |

The differing address initially suggested a dangling DNS record, which would
have made sending credentials there dangerous. It is not. The TLS certificate
was issued **2026-09-15** and covers `logger-staging.campaign-logger.com`
alongside `api.preview.campaign-logger.com`,
`app.preview.campaign-logger.com`, `profiles.preview.campaign-identity.com`
and, tellingly, `argocd.preview.cluster.jlj4.com` and
`grafana.preview.cluster.jlj4.com` — a live, actively managed GitOps preview
cluster, not a leftover.

The byte-identical swagger is the important part: staging runs the **same API
version** as production, so it is a faithful target rather than a stale fork.

**Still unknown, and it is the question that matters:** whether staging holds
separate *data*. That cannot be determined without authenticating. If it does,
most of the G2/G3/G4 guard architecture becomes belt-and-braces rather than
load-bearing. Ask Campaign Logger, or test with a staging-scoped credential.

The separate `profiles.preview.campaign-identity.com` name suggests staging has
its own identity service, which would imply separate accounts — suggestive, not
proof.

## Original 2022 evidence for Q3

`tests_live/test_logger.py` did not merely *reference*
`logger-staging.campaign-logger.com` — the recorded fixtures were **captured
from it**. The host appears in JSON:API `self` and `related` link fields inside
response bodies, which are server-generated:

```text
"self":    "https://logger-staging.campaign-logger.com/campaigns/<id>/relationships/logs"
"related": "https://logger-staging.campaign-logger.com/campaigns/<id>/logs"
```

A host serving populated JSON:API campaign responses existed at that name in
2022, which is what prompted the probe above. It still does.

## Q1 — ANSWERED: delete is soft, and reversible

The staging swagger (identical to production's) defines, for **every** resource
type — campaigns, logs, log-entries, campaign-entries, player-logs and
player-log-entries:

| Endpoint | Method | Meaning |
| --- | --- | --- |
| `/{type}/cl:deleted` | GET | list deleted objects |
| `/{type}/{id}/cl:undelete` | POST | restore a deleted object |
| `/{type}/{id}/cl:revisions/{rev}` | GET | fetch one revision |
| `/{type}/{id}/cl:head-revisions` | GET | current revision heads |
| `/{type}/{id}/cl:revision-tree` | GET | full revision history |

Thirty endpoints in total, none of which exist in `api.py`.

Section 7 of the plan recommended never running delete against the real
account, on the stated assumption that delete might be irreversible. It is not.
That recommendation should be re-argued on the new facts rather than carried
forward. Delete being recoverable is not the same as delete being free — Q2
(cascade) is still open, and an undelete still has to be performed by someone.

## Original 2022 evidence for Q1

Two distinct sources, which disagree, and the distinction matters:

**Server payloads** (`test_logger.py`, recorded from staging) carry a
`revision` attribute holding a 32-hex id, e.g.
`a22e4f4393fc4268a5913af2c1a9af79`. The same revision id repeats across several
resources. Revisions are therefore real and server-assigned, not a client-side
invention.

**Client model defaults** (`test_offline.py`) show an older `Campaign` model
with `isDeleted: False`, `deletedOn: ""`, `previousRevision: None` and
`revision: None`. These are local defaults on a model that no longer exists in
`campaign_logger.models`.

`isDeleted` and `deletedOn` appear **zero times** in the recorded server
payloads, so at the time this looked like a stale client-model artefact with
only the revision half corroborated. The swagger shows both attributes are
real on every resource; their absence from the 2022 payloads is unexplained,
and may be a sparse-fieldset or serializer difference worth noting when a live
response is finally captured.

## #44 — the field coverage table, from the swagger

Generated 2026-09-16 from the authoritative swagger, no live run required.
Collection and relationship properties are excluded; scalar attributes only.

| Resource | Modelled | Swagger attrs | Missing scalar attributes |
| --- | --- | --- | --- |
| `Campaign` | 3 | 14 | `createdOn`, `deletedOn`, `imageUrl`, `invitedPlayers`, `isDeleted`, `joinedPlayers`, `previousRevision`, `revision`, `stringId`, `updatedOn`, `userId` |
| `Log` | 4 | 14 | `createdOn`, `deletedOn`, `imageUrl`, `isDeleted`, `isPinned`, `previousRevision`, `revision`, `stringId`, `updatedOn`, `userId` |
| `LogEntry` | 4 | 16 | `createdOn`, `deletedOn`, `isDeleted`, `isShared`, `ordering`, `previousRevision`, `rawPrefix`, `rawSuffix`, `revision`, `stringId`, `updatedOn`, `userId` |
| `CampaignEntry` | 4 | 17 | `createdOn`, `deletedOn`, `isDeleted`, `labels`, `previousRevision`, `rawPublic`, `rawSummary`, `revision`, `stringId`, `tagSymbol`, `tagValueCaseInsensitive`, `updatedOn`, `userId` |
| `PlayerLog` | 4 | 14 | `createdOn`, `deletedOn`, `imageUrl`, `isDeleted`, `isPinned`, `previousRevision`, `revision`, `stringId`, `updatedOn`, `userId` |
| `PlayerLogEntry` | 4 | 16 | `createdOn`, `deletedOn`, `isDeleted`, `isShared`, `ordering`, `previousRevision`, `rawPrefix`, `rawSuffix`, `revision`, `stringId`, `updatedOn`, `userId` |

Missing from **every** resource: `createdOn`, `deletedOn`, `isDeleted`, `previousRevision`, `revision`, `stringId`, `updatedOn`, `userId`

Every resource is missing its audit trail (`createdOn`, `updatedOn`, `userId`),
its soft-delete state (`isDeleted`, `deletedOn`) and its revision pointers
(`revision`, `previousRevision`), plus `stringId`. Beyond those, the notable
per-resource gaps are `CampaignEntry.rawPublic` / `rawSummary` / `labels` and
the `rawPrefix` / `rawSuffix` / `ordering` / `isShared` set on both entry types.

## Attribute key casing — ANSWERED: the wire is kebab-case

Confirmed 2026-09-16 by a live read against the staging sandbox
(`tests/test_live_read.py`, phase 1). The server sends **kebab-case** attribute
keys on every endpoint checked — campaigns, logs, log-entries and
campaign-entries:

```
created-on  updated-on  user-id  image-url  invited-players  revision
is-pinned   is-shared   raw-text  raw-prefix  raw-suffix  raw-public
raw-summary tag-value   tag-symbol  labels  ordering
```

So the three sources disagreed and the live wire is the tie-breaker:

| source | casing |
| --- | --- |
| swagger schemas | camelCase (`campaignId`, `rawText`) |
| `tests/test_e2e.py` mocks | camelCase |
| **live wire (staging + the 2022 fixtures)** | **kebab-case** |

Consequences:

- The `_parse_*` methods hedge, e.g.
  `attrs.get("rawText", attrs.get("raw-text", ""))`. The **kebab-case fallback
  is the branch that actually fires against the server**; the camelCase branch
  exists only for the mocks. The parsers are correct because of the hedge --
  remove it in favour of camelCase and every field would silently read empty
  against the real API.
- The mocks in `test_e2e.py` are therefore **unrealistic**: they assert a casing
  the server never sends. They pass only because the hedge tolerates both. A
  fixture that mirrored the real wire would catch a regression that removed the
  fallback; worth doing when that suite is next touched.
- The real `logs` payload carries **no** `campaign-id` attribute at all, in
  either casing. `_parse_log` gets it from the JSON:API `relationships` block
  instead. The attribute-level hedge is dead code for logs; the relationship
  fallback is load-bearing.

## Pagination — partially answered (§10 Q4)

The `log-entries` listing returns top-level `meta: {"total-records": N}` and
**no** `links.next` at sandbox scale. So the API does report totals, which
strongly implies page-based access exists (`page[...]` params), but nothing
triggered a cursor at this volume.

Follow-up against staging confirmed `page[size]` and `page[number]` both work
even though the swagger documents no query parameters at all, and that
`page[size]=1000` against a 551-record collection returned all 551 with no sign
of a cap. `_get` now pages with those parameters until it holds
`meta.total-records` records (#77), so a collection larger than one page is no
longer silently truncated.

Two things remain unverified live:

- The related-resource routes (`/campaigns/{id}/logs`, `/logs/{id}/log-entries`)
  return **no** `meta` block, so there is no total to page against. `_get`
  returns those responses exactly as they arrive; whether they truncate a large
  relationship, and what they do with `page[...]`, is still unknown (#76).
- `requests` percent-encodes the brackets (`page%5Bsize%5D`), whether they are
  passed as parameters or written into the URL by hand. The hand-verified
  requests used literal brackets, so the server decoding the encoded form is
  assumed, not observed.

## What was discarded

- A hardcoded `client_id` / `api-secret` pair and a bearer JWT with an `exp` in
  2027. They are off disk here, but rotation is **deferred** by decision, so
  treat both as still live until that changes.
- Assertions frozen against one real account's data, including a campaign title
  (`Automated Log Import`), a `user-id` and campaign/log ids.
- Imports of symbols that no longer exist: `campaign_logger.models.setup`,
  `Campaign.get_all()`, `FullGeneratorModel`,
  `GeneratorClient.generate_random`.
