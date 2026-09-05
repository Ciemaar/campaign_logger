#!/usr/bin/env python
"""Give every run in a SARIF file a distinct category.

The Codacy CLI emits one SARIF file containing a separate run per tool (pylint, bandit,
prospector, remark, ...). Since 2025-07-21 the CodeQL upload action rejects a file whose
runs share a category:

    The CodeQL Action does not support uploading multiple SARIF runs with the same
    category. Please update your workflow to upload a single run per category.

A run's category comes from ``runs[].automationDetails.id`` when it is set. Codacy does not
set it, so every run lands in the same (empty) category and the upload is refused. Stamping
each run with an id derived from its tool name makes the categories distinct and leaves the
results themselves untouched.

Usage: python ci/sarif_categories.py results.sarif
"""

import json
import sys


def tool_name(run, index):
    """Return the tool name for a run, falling back to its index when absent."""
    driver = run.get("tool", {}).get("driver", {})
    return driver.get("name") or f"run-{index}"


def assign_categories(sarif):
    """Set a distinct automationDetails.id on every run. Returns the ids assigned."""
    assigned = []
    seen = {}

    for index, run in enumerate(sarif.get("runs", [])):
        name = tool_name(run, index)
        # A tool appearing twice still needs distinct ids, so disambiguate on repeat.
        seen[name] = seen.get(name, 0) + 1
        category = name if seen[name] == 1 else f"{name}-{seen[name]}"

        run.setdefault("automationDetails", {})["id"] = f"codacy/{category}/"
        assigned.append(category)

    return assigned


def main(argv):
    """Rewrite the SARIF file named in argv[1] in place."""
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2

    path = argv[1]
    with open(path, encoding="utf-8") as handle:
        sarif = json.load(handle)

    assigned = assign_categories(sarif)

    with open(path, "w", encoding="utf-8") as handle:
        json.dump(sarif, handle)

    print(f"Assigned {len(assigned)} SARIF categories: {', '.join(assigned)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
