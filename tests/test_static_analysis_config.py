"""Guard the committed static-analysis configuration against drift (issue #69).

Codacy's Pylint and the project's ruff configuration disagreed on line length and
on the pytest fixture idiom, and the resolution lived only in Codacy's dashboard.
These tests pin the file-based half of that resolution so the two tools cannot
silently diverge again.
"""

import configparser
import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PYLINTRC = REPO_ROOT / ".pylintrc"
CODACY_CONFIG = REPO_ROOT / ".codacy.yml"
PYPROJECT = REPO_ROOT / "pyproject.toml"
MANIFEST = REPO_ROOT / "MANIFEST.in"

# Codacy only detects `pylintrc` and `.pylintrc` at the repository root; it does
# not read `[tool.pylint]` from `pyproject.toml`.
CODACY_PYLINTRC_NAMES = (".pylintrc", "pylintrc")

# The analysis engines whose findings on the test tree are pytest idioms rather
# than defects. Prospector bundles its own Pylint run, and `pylint` is Codacy's
# deprecated name for the legacy Pylint 1.9 tool that still reports here.
PATH_EXCLUDED_ENGINES = ("pylintpython3", "pylint", "prospector")


def _pylintrc():
    parser = configparser.ConfigParser()
    parser.read(PYLINTRC, encoding="utf-8")
    return parser


def _ruff_line_length():
    with PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)["tool"]["ruff"]["line-length"]


def test_pylint_config_uses_a_filename_codacy_detects():
    """A Pylint config under any other name would be silently ignored."""
    present = [name for name in CODACY_PYLINTRC_NAMES if (REPO_ROOT / name).is_file()]
    assert present, f"expected one of {CODACY_PYLINTRC_NAMES} at the repository root"  # nosec


def test_pylint_line_length_matches_ruff():
    """Codacy's C0301 threshold must be the length `ruff format` actually produces."""
    assert int(_pylintrc().get("FORMAT", "max-line-length")) == _ruff_line_length()  # nosec


def test_pylint_disables_the_pytest_fixture_false_positive():
    """W0621 fires on every test that takes a fixture of the same name."""
    disabled = {code.strip() for code in _pylintrc().get("MESSAGES CONTROL", "disable").split(",")}
    assert "W0621" in disabled  # nosec


def test_every_pylint_disable_carries_a_rationale():
    """A suppression without a recorded reason is dashboard state in a new hiding place."""
    text = PYLINTRC.read_text(encoding="utf-8")
    body = text.split("[MESSAGES CONTROL]", 1)[1]
    listed = re.findall(r"^\s*([A-Z]\d{4}),?\s*$", body, flags=re.MULTILINE)
    disabled = {code.strip() for code in _pylintrc().get("MESSAGES CONTROL", "disable").split(",")}
    assert set(listed) == disabled  # nosec
    rationale = "\n".join(line for line in body.splitlines() if line.lstrip().startswith("#"))
    for code in disabled:
        assert re.search(rf"\b{code}\b", rationale), f"{code} is disabled with no rationale comment"  # nosec


def test_codacy_config_is_a_recognised_file():
    """Codacy accepts `.codacy.yml` or `.codacy.yaml`, and it must start with `---`."""
    assert CODACY_CONFIG.is_file()  # nosec
    assert CODACY_CONFIG.read_text(encoding="utf-8").startswith("---\n")  # nosec


def test_codacy_config_excludes_the_test_tree_from_pylint_engines():
    """The pytest-idiomatic findings are scoped out per engine, not repo-wide."""
    text = CODACY_CONFIG.read_text(encoding="utf-8")
    engines = text.split("engines:", 1)[1]
    for engine in PATH_EXCLUDED_ENGINES:
        block = re.search(rf"^  {re.escape(engine)}:\n((?:  .*\n|\n)*)", engines, flags=re.MULTILINE)
        assert block is not None, f"no `{engine}` engine block in .codacy.yml"  # nosec
        assert '- "tests/**"' in block.group(1), f"{engine} does not exclude the test tree"  # nosec


def test_static_analysis_config_ships_in_the_sdist():
    """check-manifest fails the `check` tox env on any tracked file the sdist omits."""
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "include .codacy.yml" in manifest  # nosec
    assert "include .pylintrc" in manifest  # nosec
