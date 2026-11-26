---
plan: 167
unit: 03
name: bridge-docs
prompt: /prompts/167-03-bridge-docs.md
iteration: 1
author: claude
reviewer: human
session: https://claude.ai/code/session_01EQrwqWTKhaaQASKkvzhmr5
pr:
verdict:
opened: 2026-11-26
reviewed:
partial:
---

# Report 167-03 — bridge-docs

- **Diff:** `2 docs files changed`, plus this report
- **Prompt:** `/prompts/167-03-bridge-docs.md`
- **Implemented by:** claude — **Verified by:** human (see Part 2)

______________________________________________________________________

## Part 1 — Implementation record

### What changed, and why

`docs/mcp_integration.rst` gains a "Bridge for sandboxes" section, written from
`src/campaign_logger/bridge.py` and its tests as they stand on the unit 02
branch (#186), and from a run of both sockets under a real systemd on
2026-11-25. It says, before any command is run, what `bridge start` creates,
writes and enables; that the default socket is read-only and cannot be made to
serve write tools; that `--write` is a separate socket, directory and unit pair
that is only started when named; the paths and modes; how to check with `bridge
status`; the sandbox-side `socat` line; and how to remove everything.
`docs/mcp-server.md` gets a short pointer to it. Campaign Logger is described as
a structured database that helps plan roleplaying games. This unit documents
unit 02's code before unit 02 merges; see Left undone.

### Criteria as claimed

<!-- mdformat off -->

| #   | criterion | command run | claimed result |
| --- | --------- | ----------- | -------------- |
| 1   | `tox -e check` passes | `uvx tox -e check` | `check: OK` |
| 2   | `tox -e docs` passes | `uvx tox -e docs` | `docs: OK` (the linkcheck step is marked ignore-outcome; see below) |
| 3   | the docs state the removal steps and that nothing starts automatically | read `docs/mcp_integration.rst`, "Removing it" and "What ``bridge start`` does" | stated, with a qualification (see Deviations) |
| 4   | the report has verbatim output of each check | this file | included below |

<!-- mdformat on -->

### Local checks at PR-open

```text
check: commands[7]> rstfmt --check AUTHORS.rst CONTRIBUTING.rst README.rst CHANGELOG.rst docs/usage.rst docs/reference/index.rst docs/installation.rst docs/readme.rst docs/contributing.rst docs/authors.rst docs/changelog.rst docs/index.rst
  check: OK (23.71=setup[0.01]+cmd[8.31,0.38,8.69,0.01,0.01,5.57,0.27,0.44] seconds)
  congratulations :) (23.77 seconds)
```

```text
build succeeded, 6 warnings.
docs: exit 1 (4.55 seconds) ... sphinx-build -b linkcheck docs dist/docs
docs: command failed but is marked ignore outcome so handling it as success
  docs: OK (8.35=setup[1.03]+cmd[1.14,1.62,4.55] seconds)
  congratulations :) (8.41 seconds)
```

The 6 build warnings are all `document isn't included in any toctree` for
existing pages, including `docs/mcp-server.md`, none caused by this change. The
linkcheck step reports three broken links, all in `readme` (the readthedocs
site, a `compare/v0.0.1...main` URL, and `docs/requirements.md`), none in the
pages this unit touches.

Order matters: `tox -e docs` leaves `dist/docs`, which `tox -e check`'s `twine
check` then rejects ("Unknown distribution format: 'docs'"). I ran `check`, then
`docs`, deleted `dist`, and ran `check` again; the output above is that final
`check`.

### Deviations from the prompt

- **No link to the hub's sandbox documentation.** The hub repository is
  private, so a hyperlink is a 404 for readers and a new broken link in the
  linkcheck step (it was, on my first attempt). The page names the hub
  repository and the two documents instead and says there is no link.
- **"No mount point invented."** The hub's pages still describe an older host
  directory (`agent-sandbox/mcp`) and mount at `/run/mcp` or `/mnt/campaign-logger`
  depending on the example. The docs use `<mount>` and say the hub's pages may
  name the older directory.
- **"Nothing starts at install or login" is qualified.** `bridge start` runs
  `enable --now` and the socket unit is `WantedBy=sockets.target`, so after you
  have run `bridge start` (or `--write`), systemd starts that socket again at
  your next login until `bridge stop` disables it. The docs say that. Nothing
  starts at install, and nothing starts until the command is run.
- **No `CHANGELOG.rst` entry.** It has one released section and no unreleased
  place, and the repo's version policy puts the changelog entry in the release PR.

### Left undone

- This branch is stacked on #186 (unit 02) and must not merge before it. If
  #186 changes, these docs need rechecking against the merged code.
- Nothing was run to check the sandbox side; the `socat` line is from the
  prompt and the hub's pages.

### Uncertain about

- Whether to point the "persists across logins" fact out more prominently. It is
  true of both sockets and matters more for the write one.
- Whether a prose reference to a private repository belongs in public docs at
  all.

### Sensitive paths touched

None. Only `docs/mcp_integration.rst`, `docs/mcp-server.md` and this report.

______________________________________________________________________

## Part 2 — Independent verification

The implementer is Claude, so there is no independent agent reviewer. See the PR
comments.
