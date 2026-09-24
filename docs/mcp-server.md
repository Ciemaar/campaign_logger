# Using the Campaign Logger MCP server

The package ships an MCP server that lets an assistant such as Claude read your
campaigns, logs and pages directly. It speaks MCP over stdio, so the client
starts it as a subprocess — there is no port to open and nothing to deploy.

## Read-only is the default

```
campaign-logger mcp            # read-only  — 12 tools
campaign-logger mcp --write    # read+write — 24 tools
```

Read-only is not a runtime check that could be argued past. The write tools are
**never registered**, so they do not appear in the tool list the assistant is
given. It cannot call `delete_campaign` because, as far as it can see, no such
tool exists.

The 12 tools available in read-only mode:

| | |
| --- | --- |
| Campaigns | `list_campaigns`, `get_campaign` |
| Logs | `list_logs`, `get_log` |
| Log entries | `list_log_entries`, `get_log_entry` |
| Pages | `list_campaign_entries`, `get_campaign_entry` |
| Generators | `list_generators`, `get_generator`, `generate_result` |
| Tag types | `get_tag_types` |

`get_*` returns the full object as JSON; `list_*` returns `id: title` summary
lines. One nuance worth knowing: `generate_result` is a POST rather than a GET —
it runs a generator and returns the result. It creates nothing and stores
nothing, which is why it is included in read-only mode, but it is the one tool
there that is not a plain read.

`get_tag_types` is the odd one out in a more useful way: it needs **no
credentials at all**, because the tag table is static. It is the only tool that
answers on a fresh install, which makes it the quickest way to confirm the client
is starting the server correctly before any keys are in place.

It is worth giving the assistant early, because it is what makes the rest of the
data legible. The API has no NPC or location model — a page carries a
`tag-symbol` and a `tag-value`, and the symbol is the type. Without the table,
"list the NPCs in this campaign" is unanswerable; with it, it means the campaign
entries whose `tag-symbol` is `@`. `docs/data-model.md` covers this in full.

The tool accepts an optional `campaign` (id or title) and **does not use it**.
Tag meanings may vary per campaign, which is not settled yet (issue #97), so the
argument exists now to keep the signature stable and the response reports
`campaign-applied: null` and a `scope` of `campaign-logger-defaults`. Read those
fields rather than assuming the answer was scoped to what you asked for.

## Credentials

The server calls the same `load_config()` the CLI uses, so it reads
**`~/.campaign_logger.json`**:

```json
{
  "client_id": "…",
  "client_secret": "…",
  "token": "…"
}
```

`client_id` / `client_secret` enable the logger tools; `token` enables the
generator tools. Either half can be absent — the corresponding tools then raise
a clear "not authenticated" error instead of failing obscurely.

Environment variables work too and **take precedence** over the file:
`CL_LOGGER_CLIENT_ID`, `CL_LOGGER_CLIENT_SECRET`, `CL_GENERATOR_TOKEN`.

Putting the credentials in `~/.campaign_logger.json` is usually easier, because
the MCP client starts the server as a subprocess and does not necessarily pass
your shell environment through.

## Claude Code

```bash
claude mcp add campaign-logger -- campaign-logger mcp
```

Everything after `--` is the command and its arguments. With credentials in
`~/.campaign_logger.json` that is the whole setup. To pass them explicitly
instead:

```bash
claude mcp add campaign-logger \
  -e CL_LOGGER_CLIENT_ID=… -e CL_LOGGER_CLIENT_SECRET=… \
  -- campaign-logger mcp
```

Check it with `claude mcp list`.

## Claude Desktop

Edit `claude_desktop_config.json` and restart Claude Desktop. The file lives at:

| OS | Path |
| --- | --- |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

```json
{
  "mcpServers": {
    "campaign-logger": {
      "command": "campaign-logger",
      "args": ["mcp"]
    }
  }
}
```

`command` must be something the desktop app can find on its own `PATH`, which is
often not your shell's `PATH`. If the server does not appear, use an absolute
path — `which campaign-logger` will tell you what it is.

To pass credentials explicitly rather than via the config file, add an `env`
block:

```json
{
  "mcpServers": {
    "campaign-logger": {
      "command": "campaign-logger",
      "args": ["mcp"],
      "env": {
        "CL_LOGGER_CLIENT_ID": "…",
        "CL_LOGGER_CLIENT_SECRET": "…"
      }
    }
  }
}
```

## Without installing: uvx

If you would rather not install the package:

```bash
claude mcp add campaign-logger -- uvx --from git+https://github.com/Ciemaar/campaign_logger campaign-logger mcp
```

or in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "campaign-logger": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/Ciemaar/campaign_logger", "campaign-logger", "mcp"]
    }
  }
}
```

This re-resolves the package on each start, so it is slower and needs network at
launch. Installing with `pipx install` or `uv tool install` is better for daily
use.

## Limiting the assistant to one campaign

**This is not currently supported, and it is worth being precise about why.**

`CL_DEFAULT_CAMPAIGN_ID` — the `default_campaign_id` key in
`~/.campaign_logger.json` — is read by `load_config()`, but **the MCP server
never consults it.** Every tool that needs a campaign takes an explicit
`campaign_id` argument, and `list_campaigns` returns every campaign on the
account. So read-only mode restricts *what* the assistant can do, not *which
campaign* it can see.

What you can do today:

- **Run read-only** (the default). Nothing can be modified, in any campaign.
- **Tell the assistant which campaign to use** — give it the id in your prompt
  or in project instructions. This is a convention, not a boundary: the
  assistant can still list and read the others if it decides to.

If you need a real boundary rather than a convention, the options are to use an
API credential scoped to a single campaign, if the service supports issuing one,
or to wait for server-side scoping. Tracked as an issue.

## Two things to be aware of

**It always talks to production.** The server constructs its client without a
base URL, so it uses `https://logger.campaign-logger.com`. There is no way to
point it at staging. For reading your real campaigns that is what you want, but
it does mean the MCP server is never exercised against the sandbox.

**Log text is not "public".** The public/private split exists for campaign
entries (pages), which carry both a `raw_public` and a `raw_text` body. Log
entries have only `raw_text`. So anything the assistant reads from a log is the
full text, regardless of the `is-shared` flag, which these tools ignore.

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| No campaign-logger tools appear | The client cannot find the command. Use an absolute path from `which campaign-logger`. |
| "Logger client not authenticated" | `CL_LOGGER_CLIENT_ID`/`CL_LOGGER_CLIENT_SECRET` absent, and `~/.campaign_logger.json` missing or lacking `client_id`/`client_secret`. |
| "Generator client not authenticated" | Same, for `token` / `CL_GENERATOR_TOKEN`. Only affects the generator tools. |
| Write tools missing | Expected — that is read-only mode. Add `--write` if you genuinely want them. |
| A large log looks truncated | The listing tools fetch everything and filter client-side, and pagination is not followed yet. See issues #76 and #77. |
