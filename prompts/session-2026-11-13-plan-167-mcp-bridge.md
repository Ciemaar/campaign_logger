---
plan: 167
unit:
name: plan-167-mcp-bridge
session: https://claude.ai/code/session_01EQrwqWNYy5TgjWPFC8kMHe
pr:
iteration: 1
---

# Session prompt — plan 167, the opt-in MCP bridge

User request (verbatim):
`/agent-repo-workflow:plan 167 coordinate with the agent in Agenticrulesandtools to adapt planning given that Jules is shutdown`

Plan the work in issue 167 as a plan in `plans/`, branch and open a draft PR.
Because Jules is shut down, ask the AgenticRulesAndTools hub session how to
assign units and write the Cost section, and follow its answers.

Hub answers (2026-11-13): use `claude` for anything dispatched today; `operator`
and `antigravity` are unvalidated; hub plan 570 labels this unit `agent`; Cost
reads "0 Jules sessions" with the reason; check commands are in
`.claude/reference/local-conventions.md`; the bridge socket path and modes are
unchanged; cite hub plan 570 (PR 584) and issues 570 and 545. Owner decisions
relayed: unix-socket bridge is the route for local MCP servers, #159 is not
planned, and Campaign Logger is a database for planning roleplaying games, not a
game runner.
