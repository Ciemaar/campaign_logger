"""``.bumpversion.cfg`` must actually work (#48).

The config had rotted three ways at once, and every one of them was silent until
someone ran the tool:

* ``current_version = 0.0.0`` while every file said ``0.0.1``, so every ``search``
  below would miss;
* a stanza for ``setup.py``, removed in the move to ``pyproject.toml``, which made
  the run die with ``FileNotFoundError``;
* no stanza for ``pyproject.toml``, which is where the packaged version now lives;
* and the ``search`` patterns for ``docs/conf.py`` and ``__init__.py`` used single
  quotes while the files use double.

So the useful test is not "does the file parse" but **"would every stanza find
what it is looking for"** -- which is exactly what the tool asserts before it
writes, and what nobody had run.
"""

import configparser
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / ".bumpversion.cfg"

FILE_SECTION = re.compile(r"^bumpversion:file(?: \([^)]*\))?:(?P<path>.+)$")


@pytest.fixture(scope="module")
def config():
    """The parsed ``.bumpversion.cfg``."""
    parser = configparser.ConfigParser()
    parser.read(CONFIG_PATH, encoding="utf-8")
    return parser


@pytest.fixture(scope="module")
def current_version(config):
    """The version bumpversion believes is current."""
    return config["bumpversion"]["current_version"]


def file_sections(config):
    """``(section_name, target_path)`` for every file stanza."""
    for name in config.sections():
        match = FILE_SECTION.match(name)
        if match:
            yield name, match.group("path").strip()


# --- the declared versions must agree ----------------------------------------


@pytest.mark.parametrize(
    "path,pattern",
    [
        ("pyproject.toml", r'^version = "(?P<version>[^"]+)"$'),
        ("src/campaign_logger/__init__.py", r'^__version__ = "(?P<version>[^"]+)"$'),
        ("docs/conf.py", r'^version = release = "(?P<version>[^"]+)"$'),
    ],
)
def test_every_declared_version_matches_the_config(current_version, path, pattern):
    """A mismatch here is what made the tool unusable, and it is invisible otherwise."""
    text = (ROOT / path).read_text(encoding="utf-8")
    found = re.search(pattern, text, re.M)
    assert found, f"{path} has no version line matching {pattern!r}"
    assert found.group("version") == current_version, f"{path} declares {found.group('version')}, .bumpversion.cfg says {current_version}"


# --- every stanza must be able to do its job ---------------------------------


def test_the_config_has_stanzas(config):
    """Anti-vacuous: the checks below iterate, so an empty config must not pass."""
    sections = list(file_sections(config))
    assert len(sections) >= 4, f"only {len(sections)} file stanzas found"


def test_every_target_file_exists(config):
    """The ``setup.py`` stanza outlived the file by two releases."""
    missing = [path for _, path in file_sections(config) if not (ROOT / path).is_file()]
    assert not missing, f".bumpversion.cfg targets files that do not exist: {missing}"


def test_every_search_pattern_is_present_in_its_target(config, current_version):
    """The check the tool makes before writing -- run here so it is run at all.

    This is what catches a quoting mismatch. A stanza whose ``search`` does not
    occur in its file is dead weight that fails the whole run, and nothing else in
    CI executes bumpversion.
    """
    unmatched = []
    for name, path in file_sections(config):
        search = config[name].get("search")
        assert search, f"{name} has no search pattern"
        needle = search.replace("{current_version}", current_version)
        if needle not in (ROOT / path).read_text(encoding="utf-8"):
            unmatched.append(f"{name}: {needle!r} not found in {path}")
    assert not unmatched, "stanzas that would fail:\n  " + "\n  ".join(unmatched)


def test_replace_patterns_mirror_their_search(config):
    """``replace`` must differ from ``search`` only in the version placeholder.

    A stanza whose replacement drifts from its search rewrites the line into a
    shape the next bump cannot find, so the breakage lands one release later.
    """
    for name, _ in file_sections(config):
        search = config[name].get("search", "")
        replace = config[name].get("replace", "")
        assert search.replace("{current_version}", "@") == replace.replace("{new_version}", "@"), (
            f"{name}: search and replace are not the same line"
        )
