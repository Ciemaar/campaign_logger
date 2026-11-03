---
plan: <N>
unit: NN
name: <slug>
repo: <owner>/<name> # Supply your repository identity here
pr:
iteration: 1
---

<!--
Everything from the first heading down is sent to Jules. `prompt-repos` strips
this frontmatter and these leading comments before dispatch, so they are for
whoever writes the prompt, not for the agent reading it.

**The first line becomes the session's name.** Jules titles a session from the
first line of what it receives, and `prompt-repos` strips the frontmatter and
these comments — so the heading below is what you will see in the Jules UI and
in `jules remote list --session`. Make it identify the unit. A constant like
`# Task` names every session identically and makes the list unreadable.

A dispatched session always checks out the default branch's HEAD server-side.
There is no way to start one from another branch — the `jules` CLI has no branch
flag, and the API's `startingBranch` is unreachable from it. So a prompt
cannot ask for a different base; if a unit needs one, it is not dispatchable yet.

Jules starts cold in a fresh VM with no memory of this repo, this plan, or any
previous iteration. Write for that reader. Density below is what buys review
time later.

**Phrase claims so they survive being acted on.**
A prompt describes a repository state that may change before dispatch, or may be
fixed by another unit before this one reaches it. Phrase claims of state so the
sentence holds whether or not the work has already happened.
Not "X is not documented. Add it." but "X should be documented. Check whether it
already is; if it is and is adequate, say so in your report and change nothing."
This matters most for claims of **absence** ("X is missing", "nothing checks Y")
because those are exactly what another unit is most likely to have fixed.
-->

# <N>-NN <slug> — <one line naming the task>

One paragraph: what to build, stated as an outcome rather than a procedure.

# Scope

**Modify only these files:**

- `src/<package>/<file>.py`
- `tests/test_<file>.py`

**Also in scope, always:** `reports/<N>-NN-<slug>.md` — your report. It is
required before you open the PR (see Report below) and is never counted against
the file list above.

**Write it from `reports/TEMPLATE.md`.** Copy that file and fill in Part 1. The
format is not decoration: the reviewer writes **Part 2** into the same document
from their own checkout, and a report with no Part 1/Part 2 split leaves them
nowhere to put it. Do not write Part 2 yourself, and do not invent a structure —
if the template does not fit what you need to say, say so in the PR description
and follow it anyway.

**Do not modify:**

- existing tests (see Test integrity below)
- dependency manifests, CI configuration
- the agents' own instruction files
- (read `## 3. The sensitive-path list` in
  `.claude/reference/local-conventions.md` when it exists, or ask rather than
  guess; read the file's `conventions-required`; if it is missing, not an
  integer, or above `1`, say so and stop)
- any plan or prompt file — those are the orchestrator's
- anything not listed above

If the task appears to require changing a file outside scope, stop and say so in
the PR description instead of doing it.

# Conventions

**Read `AGENTS.md` at the repo root before writing any code.** It is the
authority on this repository's conventions — markdown formatting, feature
tracking, session documentation, subprocess safety, review expectations. Do not
restate it here; it is in the checkout you are working in.

Use this section only for the specific reference code this task needs. Paste the
real thing, do not describe it. **Never cite code by line number**, because line
numbers go stale the moment anything above them changes. Cite a stable anchor —
the enclosing function, the class name, or a unique string to search for:

```python
# Example: how CLI commands are declared and how errors surface to the user
# (copied verbatim from src/<package>/<file>.py, in function `xyz`)
```

If the task needs no task-specific reference code beyond what `AGENTS.md`
already covers, write "None beyond `AGENTS.md`." rather than padding this
section.

# Acceptance criteria

Mechanical and checkable. Each line must be something a command can verify.
Replace the examples below with your repository's actual checks (e.g. tests,
linting, and formatting commands):

- [ ] **Example:** `npm test` passes
- [ ] **Example:** `cargo clippy` reports no new findings
- [ ] **Example:** `uv run pytest` passes
- [ ] **Example:** `uvx pre-commit run --all-files` passes
- [ ] **the report contains the verbatim output of every check above**, pasted
  as text — not a statement that they were run, and not a summary

**Do not write a criterion as a repository-wide absence.** A check of the shape
`grep -n "<thing>" -r src/` returns nothing encodes a *correction* — "remove
this" — rather than the property that must hold. It passes today and becomes
unsatisfiable the moment anything legitimately introduces that string for an
unrelated reason, and then the implementer must either fail a criterion or make
a change nobody asked for to satisfy a grep.

This is the template's existing "describe the end state, not the correction"
rule in its most common failure shape. Name the thing that must be true —
*`analyze_repo_with_gemini` calls `gemini-3.5-flash-lite`* — not the string that
must be missing from the whole tree. A past unit shipped with exactly that
defect and had to be corrected before dispatch.

Your VM clones the repository, installs dependencies and runs tests, and has
Docker available, so **run these — do not reason about what they would print.**

**CI is not runnable there.** Checks only run once a pull request exists, and
verifying them is the reviewer's step. Do not claim green checks you have not
seen.

If a criterion needs something your environment cannot provide — a GPU, an
external service, real accumulated state, a long wall-clock run — say so in the
PR description rather than simulating it or asserting the outcome.

# Anti-goals

- Do not add dependencies.
- Do not restructure modules or move files.
- Do not modify or weaken existing tests to make them pass.
- Do not reformat untouched code.
- Do not expand scope to "while I was in there" fixes.
- **Do not modify anything under `.github/` unless this task is explicitly about
  CI.** If a check is failing, fix the cause in the code. Deleting or weakening
  a workflow, downgrading an action, or removing a job is never the fix, even
  when the job is advisory and cannot block the merge.
- If the repository has a helper CLI for GitHub and Jules operations, use it
  rather than reimplementing it. Complex operations belong there; if what you
  need is missing, say so in the PR description rather than working around it.
  Any helper script you do add must follow the language rules in `AGENTS.md`. It
  must open with a header comment explaining why it exists.

# Before you finish

**Actions** — run the local checks above. If any fails, fix the cause: never by
weakening a test, deleting an assertion, disabling a hook or excluding a file,
which is the failure mode this whole review process exists to catch. If a check
fails for a reason your change did not cause, say so in the PR description and
name the evidence rather than ignoring it.

**You are not expected to check GitHub Actions.** CI runs only once the pull
request exists, and your session may have no authenticated `gh` at all. The
reviewer verifies CI.

**Deliverables** — running a check is not the same as reporting it. The verbatim
output of every command above must appear in your report as text, whatever the
result. This is a thing you produce, not a thing you do; see the report
requirement in the acceptance criteria.

**Order matters, and the obvious order fails.** If your repository runs
formatting hooks (for example, `uvx pre-commit run --all-files`), two criteria
may pull against each other: the check must pass, and its output must be pasted
into your report — but your report is a file inside the tree that command
checks, so pasting the output modifies a file the formatting hook has already
inspected. Run the checks, write the report, and then:

```bash
# Example for a pre-commit formatting hook:
uvx pre-commit run --all-files   # again, last
git add -u                       # stage whatever the hooks rewrote
git add reports/<N>-NN-<slug>.md # the report is new, so -u does not see it
uvx pre-commit run --all-files   # until clean
```

The output you pasted is from the earlier run. That is expected and correct —
what CI checks is that the tree is clean at the commit you pushed, not that your
transcript came from the final invocation. Do not resolve this by editing your
hook configuration or by excluding your report from a hook.

# Test integrity

Existing tests are the specification. If an existing test fails, the change is
wrong — do not edit the test. If a test appears genuinely incorrect, leave it
failing and explain why in the PR description.

New tests for new behaviour are welcome and should follow the conventions above.

# Answering questions

If the reviewer asks you something, **answer in the pull request** — by pushing
a commit, or by replying in the PR thread. Your session conversation is not
visible to the reviewer: they see your commits, your PR description and your PR
comments, and nothing else. An answer given only in session chat has not been
delivered.

This applies to explanations as much as to code. If you want to say why you did
something, or what you were unsure about, write it into the report or the PR
description rather than leaving it in the session.

# PR description

Include:

- which plan and unit this implements (`plan <N>, unit NN`)
- what changed and why
- anything you were unsure about
- anything you wanted to change but left alone because it was out of scope
- **anything that should become a GitHub issue.** You cannot open one; say so
  here and in your report, with enough detail that the reviewer can file it
  without asking you. A deferred concern that exists only in your head is lost.

______________________________________________________________________

<!--
This file's body froze when its PR merged — it is the record of what was asked.
Requested changes are posted as comments on the pull request, against the
session that already exists; there is no second prompt file. Only the `session`
and `pr` frontmatter fields are filled in after dispatch.
-->
