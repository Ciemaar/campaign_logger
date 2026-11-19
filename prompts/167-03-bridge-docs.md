---
plan: 167
unit: 03
name: bridge-docs
repo: Ciemaar/campaign_logger
pr:
iteration: 1
---

# 167-03 bridge-docs — document the opt-in MCP bridge

Document `campaign-logger bridge start|stop|status` as merged by units 01 and
02\. Before writing, read `src/campaign_logger/bridge.py` and the merged tests;
describe what the code does, not what the plan said. If units 01 and 02 have not
merged, stop.

# Scope

**Modify only:** `docs/mcp_integration.rst` (follow its form),
`docs/mcp-server.md` (a short pointer), and `CHANGELOG.rst` only if it has a
place for an unreleased entry. Also `reports/167-03-bridge-docs.md` from
`reports/TEMPLATE.md`, Part 1.

**Do not modify:** code, tests, `.github/`, `ci/`, `tox.ini`, `AGENTS.md`,
`.claude/`, any plan or prompt.

# Conventions

**Read `AGENTS.md` first.** The docs are checked by `mdformat --wrap 80` and
`rstfmt`; run `tox -e check`. Describe Campaign Logger as a structured database
that helps plan roleplaying games. It does not run a game; do not say it does.

# Content

- What `bridge start` writes and enables, stated before the reader runs it.
- That the default is read-only. Document `--write` separately: a different
  socket (`campaign-logger-write.sock`), what a connected agent can then change,
  that it is never started unless asked for by name, and how to remove it.
- The socket path and modes, and the sandbox-side line
  `socat STDIO UNIX-CONNECT:/run/mcp/campaign-logger.sock`.
- How to check (`bridge status`) and how to remove it: `bridge stop`, delete the
  two unit files under `~/.config/systemd/user/`,
  `systemctl --user daemon-reload`.
- Nothing starts at install or login.
- A link to the hub's sandbox documentation (Ciemaar/AgenticRulesAndTools) for
  the sandbox side; do not copy it.

# Acceptance criteria

- [ ] `tox -e check` passes
- [ ] `tox -e docs` passes
- [ ] the docs state the removal steps and that nothing starts automatically
- [ ] the report contains the verbatim output of each check, as text

# Anti-goals

No code changes, no new dependencies, no rewriting unrelated documentation.

# Before you finish

Run the checks, write the report, rerun `tox -e check`.

# Test integrity

No test changes.

# Answering questions

Put questions in the PR description.
