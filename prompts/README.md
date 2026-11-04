# Prompts

What an implementing agent was actually told, kept verbatim.

- `TEMPLATE.md` — copy this to start a unit prompt
- `<N>-NN-<slug>.md` — one prompt per unit of work
- `session-YYYY-MM-DD-<slug>.md` — composite prompt for a Claude session
- `archive/` — prompts whose plan has been archived

**A unit prompt is written with its plan and reviewed in the plan's PR**, then
frozen at dispatch. The body is the record of what was asked, and the only way
to later tell a bad implementation from a bad instruction. Its `session` and
`pr` frontmatter fields are mutable metadata. Requested changes go in PR
comments against the existing session; there is no second prompt file.

A unit whose prompt cannot be written yet carries `prompt: null` and
`status: blocked`; its prompt arrives later in its own PR.

**A session prompt is the opposite** — a living document, rewritten as the
session progresses. `AGENTS.md`'s rule on session-prompt documentation has the
rule.

If you are implementing a unit: your prompt is the specification, and the whole
file was sent to you, frontmatter and comments included. How prompts get written
and dispatched is in `ORCHESTRATION.md`, which is not yours to follow.
