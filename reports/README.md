# Reports

What was built, and what was independently verified. **One report per unit**,
updated in place across re-reviews, named to match its prompt.

- `TEMPLATE.md` — copy this to start a report
- `<N>-NN-<slug>.md` — the report for one unit, for its whole lifetime
- `session-YYYY-MM-DD-<slug>.md` — what a Claude session actually did
- `archive/` — reports whose plan has been archived

**Part 1** is written by the implementer at PR-open and never revised
afterwards. **Part 2** is written by the reviewing agent from its own checkout.
A human never fills in either — human judgement goes in PR comments, where the
person is already reading the diff.

`AGENTS.md`'s rule to write the report when you are ready to open the PR, before
opening it, states the implementer's obligation, including why the timing
matters. Write Part 1 honestly, including the parts that do not flatter the
change: a report recording only successes is indistinguishable from one that was
not written.
