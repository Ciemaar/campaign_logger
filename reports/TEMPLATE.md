---
plan: <N>
unit: NN
name: <slug>
prompt: /prompts/<N>-NN-<slug>.md
iteration: 1
author:              # jules | claude — whoever implemented and opened the PR
reviewer:            # claude | <human> — whoever verified it
session:
pr:
verdict:             # set by the reviewer: approve | request-changes | escalate
opened: YYYY-MM-DD   # this file is written before the PR exists
reviewed:
partial:             # true only for a report covering part of a plan
---

<!--
Created by the implementing agent when it is ready to open the PR — before
running `gh pr create`, not after. A PR without a report is incomplete work.

Written in two parts by two different authors. Part 1 is a claim; Part 2 is
evidence. Keeping them separate is the entire point of the format — do not merge
them, and do not let Part 2 quote Part 1.

One report per unit, updated in place across re-reviews. Part 1 is never
revised; Part 2 is replaced, and the "Fixed since last review" section keeps the
history of what each round raised.
-->

# Report <N>-NN — <slug>

- **Diff:** `N files changed, +N/-N`
- **Prompt:** `/prompts/<N>-NN-<slug>.md`
- **Implemented by:** \<jules | claude> — **Verified by:** \<claude | human>

______________________________________________________________________

## Part 1 — Implementation record

*Written by the implementing agent, before opening the PR. This is a
self-report: a statement of what the author believes and intends, not evidence
that any of it is true.*

### What changed, and why

One paragraph. The reasoning, not a restatement of the diff.

### Criteria as claimed

<!-- mdformat off -->

| #   | criterion                  | command run | claimed result   |
| --- | -------------------------- | ----------- | ---------------- |
| 1   | Example: `npm test` passes | `npm test`  | `N passed in Ns` |

<!-- mdformat on -->

### Local checks at PR-open

What you ran in your own session, with real output. **Not CI** — CI does not run
until the pull request exists, so it cannot appear here; the reviewer records it
in Part 2. Read `## 1. The check commands` in
`.claude/reference/local-conventions.md` when it exists, or ask rather than
guess; read the file's `conventions-required`; if it is missing, not an integer,
or above `1`, say so and stop.

<!-- mdformat off -->

| check      | command                                   | result             |
| ---------- | ----------------------------------------- | ------------------ |
| tests      | Example: `npm test`                       | `N passed in Ns`   |
| lint       | Example: `cargo clippy`                   | clean / N findings |
| types      | Example: `tsc --noEmit`                   | clean / N errors   |
| formatting | Example: `uvx pre-commit run --all-files` | pass / fail        |

<!-- mdformat on -->

If anything failed, say whether this change caused it and what you did.

### Deviations from the prompt

Anywhere the implementation differs from what was asked, and why. "None" is a
valid answer; silence is not.

### Left undone

Anything in scope that was not finished, and anything the author wanted to
change but left alone because it was out of scope.

### Uncertain about

What the author guessed at. This is the section that most often predicts where
review finds a problem — write it honestly rather than defensively.

______________________________________________________________________

## Part 2 — Independent verification

*Written by the **reviewing agent** against a fresh checkout of the branch —
never by a human. Reports are agent artifacts end to end; human judgement goes
in PR comments, where the person is already reading the diff.*

*Every row below must be a command the reviewer ran. Do not copy Part 1's table
— re-derive it. The author's self-report is not evidence, and a reviewer who
transcribes it has verified nothing.*

*If the implementer was Claude, there is no independent agent reviewer. Replace
this part with one line saying so and pointing at the PR comments. Do not leave
it blank as though someone will fill it in.*

### Criteria as verified

<!-- mdformat off -->

| #   | criterion                  | command run | actual output    | verdict |
| --- | -------------------------- | ----------- | ---------------- | ------- |
| 1   | Example: `npm test` passes | `npm test`  | `N passed in Ns` | PASS    |

<!-- mdformat on -->

### CI checks

Verified by the reviewer once the PR exists — the implementer could not see
these. Name each check and its outcome; "green" with nothing named is not a
record.

<!-- mdformat off -->

| check                         | outcome     | run    |
| ----------------------------- | ----------- | ------ |
| `pre-commit`                  | pass / fail | <link> |
| `test (3.12)` … `test (3.15)` | pass / fail | <link> |

<!-- mdformat on -->

### Fixed since last review

Only on a re-review. Each item raised previously and what happened to it. A
criterion that has now failed twice is the signal that the spec is wrong rather
than the code.

<!-- mdformat off -->

| finding | implementer's reply | resolution (fixed / outstanding) |
| ------- | ------------------- | -------------------------------- |
|         |                     |                                  |

<!-- mdformat on -->

### Discrepancies with Part 1

Anywhere the verified result differs from the claimed one — including criteria
the author reported passing that the reviewer could not reproduce. Divergence
here is the highest-signal finding in the whole document; a report that never
records any is either lucky or not being read.

### Diff review

- **Scope drift:** anything in the diff the prompt did not ask for, file by
  file. "None" is an acceptable answer; a blank section is not.
- **Convention drift:** does this read like the rest of the codebase, or like
  generically correct code from a model that had never seen it? Cite the file.
- **Test integrity:** were any existing tests modified, deleted, or had
  assertions weakened? This is a hard failure, not a note.
- **Sensitive paths:** check the diff against the plan's list. Name any hit.

### Does this serve the plan?

The separate pass from `review.md` step 8, kept apart from the criteria above
because a unit can satisfy every criterion and be aimed at the wrong target. One
of three:

- **Serves the intent** — say so in a sentence.
- **Serves the intent and improves on the prompt** — name the improvement and
  the criteria change it implies. Do not grade a better answer down for failing
  to match a worse specification.
- **Does not serve the intent** — name what would, and say whether the fault is
  in the **prompt** or the implementation. A unit that did exactly what its
  prompt said and still missed the intent is a prompt finding, and saying so is
  what stops a re-dispatch reproducing it.

"I would have done it differently" is not a finding.

### Unverifiable

What could not be checked mechanically, and why. This section is the point of
the report — do not bury it under the criteria table, and do not leave it empty
unless every criterion really was a command.

### Verdict and rationale

`approve` | `request-changes` | `escalate`, and the reason in one paragraph.

### Process observations

How the machinery itself performed, stage by stage — plan, dispatch, review,
archive. We are developing this process, so this section is data, not filler.
Record what happened rather than what should have happened, and say "nothing
notable" where that is true rather than inventing something.

These feed the workflow's revision mechanism. An observation not recorded here
cannot be cited in future process improvements, and therefore does not get
fixed.

### Prompt lessons

What in the prompt allowed any drift found above. Feeds the plan's Outcome
section on archive.
