# Live testing: salvaged evidence

Evidence extracted from the untracked `tests_live/` directory before it was
deleted under Phase 0.4 of the live-server test plan (issue #62). The directory
held hardcoded live credentials and could not be imported against `main`, so it
was removed; this file preserves the only parts worth keeping.

Everything below is **evidence, not confirmed behaviour**. The payloads were
recorded by hand in 2022 against a host that may no longer exist. Each item is
tied to the open question it bears on in §10 of the plan.

## Q3 — is there a staging host? Evidence: yes, in 2022

`tests_live/test_logger.py` did not merely *reference*
`logger-staging.campaign-logger.com` — the recorded fixtures were **captured
from it**. The host appears in JSON:API `self` and `related` link fields inside
response bodies, which are server-generated:

```
"self":    "https://logger-staging.campaign-logger.com/campaigns/<id>/relationships/logs"
"related": "https://logger-staging.campaign-logger.com/campaigns/<id>/logs"
```

A host that serves populated JSON:API campaign responses existed at that name.
Whether it still exists, whether the current credentials reach it, and whether
it holds separate data are all still unknown.

This raises Q3's priority: the plan already called a real staging host "a far
better answer than every guard in §2", and this is evidence it is worth asking
about rather than assuming.

## Q1 — soft delete and revisions

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

Critically, `isDeleted` and `deletedOn` appear **zero times** in the recorded
server payloads. So the soft-delete hint comes only from a stale client model,
while the revision system is corroborated by real server output. Q1 remains
open, and the weaker half of its evidence is weaker than it first appeared.

## New: attribute key casing is unresolved (bears on #44 and §5)

The recorded staging payloads use **kebab-case** attribute keys:

```
"image-url", "invited-players", "created-on", "updated-on", "user-id", "revision"
```

The mocked fixtures in `tests/test_e2e.py` use **camelCase** (`campaignId`,
`rawText`), and `_parse_campaign` (`api.py:213`) reads only `title` and
`description` — both casing-neutral. `_parse_log` (`api.py:228`) already hedges:

```python
campaign_id = str(attrs.get("campaignId", attrs.get("campaign-id", "")))
```

That hedge is the tell: the codebase does not know which casing the server
sends, and the mocks assert one while the only real recorded payload shows the
other. The Phase 1 capture in §5 should settle this first, because every
`_parse_*` method depends on it and the #44 field table cannot be written until
it is known.

Also visible in the staging payloads but absent from every current model:
`created-on`, `updated-on`, `image-url`, `invited-players`, `user-id`. These
belong in the #44 coverage table as candidate gaps.

## What was discarded

- A hardcoded `client_id` / `api-secret` pair and a bearer JWT with an `exp` in
  2027. They are off disk here, but rotation is **deferred** by decision, so
  treat both as still live until that changes.
- Assertions frozen against one real account's data, including a campaign title
  (`Automated Log Import`), a `user-id` and campaign/log ids.
- Imports of symbols that no longer exist: `campaign_logger.models.setup`,
  `Campaign.get_all()`, `FullGeneratorModel`,
  `GeneratorClient.generate_random`.
