"""Tests for ci/sarif_categories.py, the fix for the SARIF upload failure in #35."""

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parent.parent / "ci" / "sarif_categories.py"


@pytest.fixture(scope="module")
def sarif_categories():
    """Load ci/sarif_categories.py, which is a script rather than a package module."""
    spec = importlib.util.spec_from_file_location("sarif_categories", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sarif(*names):
    return {"runs": [{"tool": {"driver": {"name": name}}, "results": []} for name in names]}


def test_each_run_gets_a_distinct_category(sarif_categories):
    """The Codacy multi-tool case: every run must end up in its own category."""
    sarif = _sarif("PyLint", "Bandit", "Prospector", "remark-lint")

    assigned = sarif_categories.assign_categories(sarif)

    ids = [run["automationDetails"]["id"] for run in sarif["runs"]]
    assert len(set(ids)) == len(ids)  # nosec - the whole point of #35
    assert assigned == ["PyLint", "Bandit", "Prospector", "remark-lint"]  # nosec


def test_repeated_tool_names_are_disambiguated(sarif_categories):
    """Two runs from the same tool would otherwise collide again."""
    sarif = _sarif("Bandit", "Bandit")

    sarif_categories.assign_categories(sarif)

    ids = [run["automationDetails"]["id"] for run in sarif["runs"]]
    assert ids[0] != ids[1]  # nosec


def test_run_without_a_tool_name_still_gets_a_category(sarif_categories):
    """A malformed run must not collapse into the shared empty category."""
    sarif = {"runs": [{"results": []}, {"results": []}]}

    sarif_categories.assign_categories(sarif)

    ids = [run["automationDetails"]["id"] for run in sarif["runs"]]
    assert len(set(ids)) == 2  # nosec


def test_results_are_not_modified(sarif_categories):
    """Only automationDetails is added; findings must pass through untouched."""
    finding = {"ruleId": "Bandit_B101", "message": {"text": "assert used"}}
    sarif = {"runs": [{"tool": {"driver": {"name": "Bandit"}}, "results": [finding]}]}

    sarif_categories.assign_categories(sarif)

    assert sarif["runs"][0]["results"] == [finding]  # nosec


def test_existing_automation_details_are_preserved_alongside_the_id(sarif_categories):
    """Existing automationDetails keys must survive the id being added."""
    sarif = {"runs": [{"tool": {"driver": {"name": "PyLint"}}, "automationDetails": {"description": {"text": "x"}}}]}

    sarif_categories.assign_categories(sarif)

    details = sarif["runs"][0]["automationDetails"]
    assert details["description"] == {"text": "x"}  # nosec
    assert details["id"] == "codacy/PyLint/"  # nosec
