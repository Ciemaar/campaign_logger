"""Tests for ci/sarif_categories.py, the fix for the SARIF upload failure in #35."""

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

MODULE_PATH = Path(__file__).resolve().parent.parent / "ci" / "sarif_categories.py"


@pytest.fixture(scope="module")
def sarif_categories() -> ModuleType:
    """Load ci/sarif_categories.py, which is a script rather than a package module."""
    spec = importlib.util.spec_from_file_location("sarif_categories", MODULE_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - import plumbing
        raise RuntimeError(f"could not load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sarif(*names: str) -> dict[str, Any]:
    """Build a SARIF document with one empty run per named tool."""
    runs: list[dict[str, Any]] = [{"tool": {"driver": {"name": name}}, "results": []} for name in names]
    return {"version": "2.1.0", "runs": runs}


def _ids(sarif: dict[str, Any]) -> list[str]:
    """Return the automationDetails id of every run."""
    return [run["automationDetails"]["id"] for run in sarif["runs"]]


def test_each_run_gets_a_distinct_category(sarif_categories: ModuleType) -> None:
    """The Codacy multi-tool case: every run must end up in its own category."""
    sarif = _sarif("PyLint", "Bandit", "Prospector", "remark-lint")

    assigned = sarif_categories.assign_categories(sarif)

    ids = _ids(sarif)
    assert len(set(ids)) == len(ids)  # nosec - the whole point of #35
    assert assigned == ["PyLint", "Bandit", "Prospector", "remark-lint"]  # nosec


def test_repeated_tool_names_are_disambiguated(sarif_categories: ModuleType) -> None:
    """Two runs from the same tool would otherwise collide again."""
    sarif = _sarif("Bandit", "Bandit")

    sarif_categories.assign_categories(sarif)

    ids = _ids(sarif)
    assert ids[0] != ids[1]  # nosec


def test_run_without_a_tool_name_still_gets_a_category(sarif_categories: ModuleType) -> None:
    """A malformed run must not collapse into the shared empty category."""
    sarif: dict[str, Any] = {"runs": [{"results": []}, {"results": []}]}

    sarif_categories.assign_categories(sarif)

    assert len(set(_ids(sarif))) == 2  # nosec


def test_results_are_not_modified(sarif_categories: ModuleType) -> None:
    """Only automationDetails is added; findings must pass through untouched."""
    finding = {"ruleId": "Bandit_B101", "message": {"text": "assert used"}}
    sarif: dict[str, Any] = {"runs": [{"tool": {"driver": {"name": "Bandit"}}, "results": [finding]}]}

    sarif_categories.assign_categories(sarif)

    assert sarif["runs"][0]["results"] == [finding]  # nosec


def test_existing_automation_details_are_preserved(sarif_categories: ModuleType) -> None:
    """Existing automationDetails keys must survive the id being added."""
    sarif: dict[str, Any] = {"runs": [{"tool": {"driver": {"name": "PyLint"}}, "automationDetails": {"description": {"text": "x"}}}]}

    sarif_categories.assign_categories(sarif)

    details = sarif["runs"][0]["automationDetails"]
    assert details["description"] == {"text": "x"}  # nosec
    assert details["id"] == "codacy/PyLint/"  # nosec


def test_main_writes_a_new_file_and_leaves_the_source_alone(sarif_categories: ModuleType, tmp_path: Path) -> None:
    """The source is root-owned in CI, so it must never be opened for writing (#35)."""
    source = tmp_path / "results.sarif"
    destination = tmp_path / "results.categorised.sarif"
    source.write_text(json.dumps(_sarif("PyLint", "Bandit")), encoding="utf-8")
    source.chmod(0o444)

    exit_code = sarif_categories.main(["sarif_categories.py", str(source), str(destination)])

    assert exit_code == 0  # nosec
    assert json.loads(source.read_text(encoding="utf-8")) == _sarif("PyLint", "Bandit")  # nosec
    assert len(set(_ids(json.loads(destination.read_text(encoding="utf-8"))))) == 2  # nosec


def test_main_rejects_the_wrong_number_of_arguments(sarif_categories: ModuleType) -> None:
    """Guards against the workflow being wired up with the old single-argument form."""
    assert sarif_categories.main(["sarif_categories.py", "only-one.sarif"]) == 2  # nosec
