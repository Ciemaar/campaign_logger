# Configuring Codacy for a Python repository

Written while aligning Codacy with this repository's own conventions (issue
#69). It is deliberately repo-agnostic: the intent is that another project can
follow it without re-deriving any of it. Claims here were checked against
Codacy's documentation; where something is an observation from this repository
rather than documented behaviour, it says so.

## 1. The two things called "Codacy"

These are separate integrations and confusing them wastes a lot of time.

| | Codacy **app** (the PR check) | Codacy **SARIF upload** (code scanning) |
| --- | --- | --- |
| What it is | Codacy's servers analyse each push and post a status check | A GitHub Action that uploads results into GitHub's code-scanning UI |
| Shows up as | the `Codacy Static Code Analysis` check on a PR | alerts under Security → Code scanning |
| Configured by | the Codacy dashboard plus committed config files | a workflow file in `.github/workflows/` |
| Turning one off | does nothing to the other | does nothing to the other |

A repository can have either, both, or one that was removed while the other
kept running. **Alerts still visible in GitHub's code-scanning list can be
stale** — if the uploading workflow was deleted, nothing refreshes or closes
them, and they will not match what the PR check reports today.

**Diagnose from the PR check, not from code scanning.** The check's annotations
are what actually gates a merge:

```bash
HEAD=$(gh pr view <PR> --json headRefOid --jq .headRefOid)
CRID=$(gh api "repos/<owner>/<repo>/commits/$HEAD/check-runs" \
        --jq '.check_runs[] | select(.name|test("Codacy";"i")) | .id' | head -1)
gh api "repos/<owner>/<repo>/check-runs/$CRID/annotations" \
        --jq '.[] | "\(.path):\(.start_line)\t\(.message)"'
```

Grouping those messages is usually enough to identify the cause:

```bash
gh api ".../check-runs/$CRID/annotations" --jq '.[].message' | sort | uniq -c | sort -rn
```

## 2. What can live in the repository, and what cannot

Codacy's settings are split between the dashboard and committed files, and the
split is not intuitive.

| Setting | Where it lives |
| --- | --- |
| Which tools are enabled | **Dashboard only** (Code patterns) |
| Which individual patterns are enabled | **Dashboard only** |
| Whether a tool reads its native config file | **Dashboard only** (a per-tool "Configuration file" toggle) |
| Per-tool and per-pattern options (line length, naming, disables) | The tool's own config file, but **only while that toggle is on** |
| Path exclusions | `.codacy.yml`, globally or per engine |
| Duplication / complexity thresholds, languages | `.codacy.yml` |

The last three rows are quoted from the specification (§3). The first three are
reported behaviour I could not confirm against a reachable doc page — see the
confidence note in §4.

The practical consequence: **you cannot make a repository's Codacy behaviour
fully declarative.** At minimum someone has to flip the per-tool "Configuration
file" toggles once. Plan for a short dashboard checklist in the PR description
rather than assuming a committed file is sufficient.

## 3. `.codacy.yml`

Verified against Codacy's [configuration file
specification](https://docs.codacy.com/repositories-configure/codacy-configuration-file/).

- Lives at the repository root, named `.codacy.yml` or `.codacy.yaml`.
- Must begin with a `---` line.
- Top-level keys: `engines`, `languages`, `exclude_paths`, `include_paths`.
- Per-engine keys: `exclude_paths`, `base_sub_dir`, `config`, and
  language-specific options.
- `exclude_paths` patterns use **Java glob syntax**.
- `include_paths` specifies exceptions to `exclude_paths`, and can pull back
  files excluded by default.

```yaml
---
exclude_paths:
  - "vendor/**"

engines:
  pylintpython3:
    exclude_paths:
      - "tests/**"
```

What it **cannot** do:

> "The Codacy configuration file lets you configure tools, but you can't enable
> or disable them. A tool can only be enabled or disabled on the Code patterns
> page."

Note what that quote does *not* say. It is about **tools**, not individual
patterns. Whether a single pattern can be toggled from this file is not stated
either way on that page — do not assume it can.

The per-engine `config` key exists, but the specification **does not document
what it accepts**, and its one example is inline settings
(`config: {languages: [ruby]}`) rather than a path. Treat
`engines: pylint: config: .pylintrc` — a form that circulates in blog posts —
as unsupported until you have seen it work, and use the native-config route in
§4 instead.

> **Trap.** Codacy states plainly:
>
> > "If your repository has a Codacy configuration file, the Ignored files
> > settings defined on the Codacy UI don't apply and you must ignore files
> > using the configuration file instead."
>
> So anything still wanted in that UI list must be restated in `exclude_paths`.
> Check it *before* committing the file — this is the one way adding it can
> *surface* findings rather than reduce them.

## 4. Native tool configuration

> ⚠️ **Confidence note.** Everything in this section is reported behaviour that
> I could **not** confirm against a reachable documentation page — the relevant
> Codacy doc URLs redirected or 404'd at the time of writing. The
> `.codacy.yml` details in §3 are quoted from the live specification and are
> solid; treat this section as a starting hypothesis and verify against the
> Code patterns page for your own repository before relying on it.

Codacy will read a tool's own config file, but only while that tool's
"Configuration file" toggle is enabled on the Code patterns page. Turning it on
is also reported to **replace Codacy's curated pattern selection with the
tool's own defaults**, which usually means new categories of finding appear.
Triage those before flipping it, not after.

Filenames reportedly matter, because Codacy looks for specific ones:

| Tool | Config files Codacy looks for |
| --- | --- |
| Pylint | `pylintrc`, `.pylintrc` — **not** `[tool.pylint]` in `pyproject.toml` |
| Ruff | `pyproject.toml`, `ruff.toml`, `.ruff.toml` |

Engine names are their own hazard. For Pylint the current engine is
**`pylintpython3`**; a bare `pylint` refers to the deprecated Pylint 1.9 tool.
A repository can have **both enabled at once**, which produces duplicate
findings plus checks the modern Pylint removed years ago (`C0326`, `C0330` are
the usual giveaways). If those codes appear, the legacy tool is on — turn it
off rather than configuring around it.

## 5. The failure mode to look for first: convention conflict

The most common reason a Codacy check fails on a well-maintained repository is
not a defect. It is Codacy running a tool with a **different convention** from
the one the repository enforces, so the two demand mutually exclusive things and
no amount of code editing satisfies both.

A worked example from this repository. Codacy reported 30 findings on one PR,
all "Documentation":

| annotation | count |
| --- | --- |
| Multi-line docstring summary should start at the second line (D213) | 12 |
| Section name should end with a newline (`Returns`, not `Returns:`) | 6 |
| Missing dashed underline after section (`Returns`) | 6 |
| Missing blank line after last section (`Returns`) | 6 |

Read individually, the first looks like a formatting nit. Read together, the
last three are **numpydoc** requirements — so Codacy's docstring checking was
set to the numpy convention while the project sets `convention = "google"`
under `[tool.ruff.lint.pydocstyle]`. Under google, `Returns:` takes a colon and
no underline, and `D212` puts the summary on the *first* line, which is the
exact opposite of `D213`.

Reformatting to satisfy Codacy would have broken the repository's own lint gate.
The fix was configuration: enable Ruff's "Configuration file" toggle so Codacy
reads `pyproject.toml`, and all four stop firing together.

**The lesson worth carrying:** when several findings look like unrelated style
nits, check whether they are one convention disagreement wearing several hats.
Counting the annotation types is what makes it visible.

## 6. Setting up a new repository

1. Look at the PR check's annotations first (§1) and group them. Do not start
   from the code-scanning alert list; it may be stale or from a different tool.
2. Separate **defects** from **convention disagreements**. Fix the first in
   code; configure the second. Never reformat code to satisfy a tool that
   contradicts the repository's own linter.
3. Before adding `.codacy.yml`, copy anything still wanted out of the UI
   "Ignored files" list.
4. Add `.codacy.yml` with per-engine `exclude_paths` for directories where the
   project deliberately writes differently (test trees especially).
5. Add the native tool config (`.pylintrc`, and for Ruff just keep using
   `pyproject.toml`), with a rationale comment beside every suppression.
6. Flip the per-tool "Configuration file" toggles. Nothing in step 5 takes
   effect until you do.
7. Disable the legacy Pylint tool if `C0326`/`C0330` are showing.
8. Pin the parts that can drift with a test — that a committed
   `max-line-length` still equals the linter's `line-length`, for instance.
   Otherwise the two silently diverge again.
9. Add the config files to `MANIFEST.in` if the project runs `check-manifest`.

## 7. Findings that are usually configuration, not defects

Observed in this repository; the reasoning generalises.

| Finding | Why it is usually not a defect |
| --- | --- |
| `W0621` redefined-outer-name | A pytest test taking a fixture of the same name. Idiomatic; renaming makes tests worse. |
| `C0116` / `C0114` missing docstring | Usually only in test trees, which most projects already exempt from their own docstring rules. |
| `C0103` invalid-name | Typically `e`, `f`, or comprehension variables. |
| `E1136` unsubscriptable-object | False positive on PEP 585 builtins (`dict[str, Any]`) from an old astroid. |
| `B101` (Bandit) | `assert` in tests, which is what pytest is. |
| `R0903` too-few-public-methods | Pydantic models and dataclasses. |

Each should still carry a rationale where it is suppressed. A suppression
without a reason is indistinguishable from a bug being hidden.
