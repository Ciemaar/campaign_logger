# Plans

A plan is the durable record of a piece of work: what we intend to do, why,
broken into units small enough that each is one reviewable PR.

- `TEMPLATE.md` — copy this to start a new plan
- `<N>-<slug>.md` — active plans, where `<N>` is the GitHub issue implemented
- `archive/` — plans whose every unit is merged or dropped, Outcome filled in

Plans sit alongside two siblings, keyed by the same ID — `/prompts/` records
what the implementer was told, `/reports/` records what was verified. Given any
one file you can find the other two by name.

## If you are implementing a unit

You do not need this directory. Read your prompt in `/prompts/`, follow
`AGENTS.md`, and write `/reports/<N>-NN-<slug>.md` before you open your PR. Do
not edit the plan — its status fields are the orchestrator's.

## If you are orchestrating

Everything — lifecycle, ID scheme, status values, who implements, dispatch,
review, archival — is in the workflow plugin's `ORCHESTRATION.md`, with the
`/plan`, `/dispatch`, `/review` and `/archive-plans` commands beside it.
