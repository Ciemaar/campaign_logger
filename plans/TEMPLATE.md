---
id: <N>
issues: [NNN]         # every issue this plan implements, the invoked one first;
                      # that first element is the ID, so a single-issue plan
                      # lists one number equal to `id`
title: <short imperative title>
status: draft
created: YYYY-MM-DD
updated: YYYY-MM-DD
units:
  - name: <slug>
    assignee: jules      # jules | claude — who implements this unit
    prompt: /prompts/<N>-01-<slug>.md   # written with this plan; null if blocked
    report:              # /reports/<N>-01-<slug>.md, written at PR-open
    pr:                  # informational; `sessions list` is authoritative
    status: pending      # pending | blocked | dispatched | in-review | merged | dropped
    depends_on: []
---

# <N> — <title>

## Intent

What we are trying to achieve and why, in a few sentences. Written for someone
who has not been in the conversation.

## Current state

What the code does today. Name the specific files and functions involved so the
plan is checkable against the repo, not just plausible.

## Approach

The decomposition and its rationale. Why these units, in this order. Call out
which units are independent (dispatch in parallel) and which are sequenced.

## Units

### 01 — <slug>

- **Scope:** files in bounds
- **Out of scope:** explicit do-not-touch list
- **Acceptance criteria:** mechanical, checkable — each one a command your
  repository actually runs (for example: `npm test`, `cargo clippy`, or
  `uv run pytest` — read `## 1. The check commands` in
  `.claude/reference/local-conventions.md` when it exists, or ask rather than
  guess; read the file's `conventions-required`; if it is missing, not an
  integer, or above `1`, say so and stop). A criterion must describe the
  property that must hold (the end state), not the specific correction to make.
  See prompt for the full list.
- **Depends on:** none

### 02 — <slug>

...

Keep each unit small enough to be one reviewable PR. A unit that produces a
900-line diff was three units.

## Sensitive paths

Any diff touching these escalates to a human regardless of test results. These
are the categories that typically require human oversight; extend them per plan,
and remove one only with a stated reason (read `## 3. The sensitive-path list`
in `.claude/reference/local-conventions.md` when it exists, or ask rather than
guess; read the file's `conventions-required`; if it is missing, not an integer,
or above `1`, say so and stop):

- dependency manifests
- CI configuration
- credential handling
- the agents' own instruction files

Trim or extend this list per plan — but do not leave it empty.

## Risks and unknowns

What could go wrong, and what this plan is guessing about. Be specific; "might
be tricky" is not a risk.

## Not doing

Adjacent work deliberately excluded from this plan, so nobody has to re-litigate
it during review.

## Outcome

<!-- Fill in before archiving. Delete this comment. -->

- **Shipped:** what actually merged
- **Dropped:** which units were abandoned and why
- **Deviations:** where the implementation differs from the plan
- **Prompt lessons:** what to change in future prompts. This is the part that
  compounds — if a review found scope drift or convention drift, say what in the
  prompt allowed it.
