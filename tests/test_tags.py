"""The tag symbols are the type system for campaign content, so pin them.

A consumer asking for "the NPCs" is really asking for campaign entries whose
``tag_symbol`` is ``@``. That makes this mapping an interface, not a detail.
"""

import re
from pathlib import Path

import pytest

from campaign_logger.rag_export import SYMBOL_LEGEND as EXPORTER_LEGEND
from campaign_logger.tags import NOTE_TAG_SYMBOL
from campaign_logger.tags import SYMBOL_LEGEND
from campaign_logger.tags import TAG_NAMES
from campaign_logger.tags import TAG_TYPES
from campaign_logger.tags import render_legend
from campaign_logger.tags import tag_name


def test_legend_is_byte_identical_to_the_historical_header():
    """The exporter's output is byte-compared against the notebook it replaced.

    Rendering the legend from a mapping is only safe if it renders to exactly
    what was written by hand before.
    """
    expected = (
        "Prefixes\n\n"
        "@ - Cast of Characters - People\n"
        "^ - Organizations\n"
        "# - Gazetteer - Locations\n"
        "$ - Money\n"
        "! - Quartermaster - Equipment, Gear, Weapons\n"
        "% - Calendar\n"
        "* - Loopy Planning - Plot\n"
        "~ - Rules/Spells\n"
        "§ - Sections\n"
        "+ - Pluses\n"
        "- - Minuses\n"
        "& - Notes\n"
    )
    assert SYMBOL_LEGEND == expected  # nosec
    assert EXPORTER_LEGEND is SYMBOL_LEGEND  # nosec  the exporter uses this one


def test_every_symbol_has_both_a_label_and_a_short_name():
    assert set(TAG_TYPES) == set(TAG_NAMES)  # nosec


@pytest.mark.parametrize(("symbol", "name"), [("@", "people"), ("#", "locations"), ("*", "plot"), ("&", "notes")])
def test_tag_name_maps_the_symbols_consumers_ask_for(symbol, name):
    """These four are the ones an external consumer maps onto its own model."""
    assert tag_name(symbol) == name  # nosec


@pytest.mark.parametrize("absent", [None, "", "§§", "Z"])
def test_tag_name_returns_none_rather_than_raising(absent):
    """The symbol set is Campaign Logger's and may grow.

    A consumer classifying a page it does not recognise should be able to skip
    it, not crash on it.
    """
    assert tag_name(absent) is None  # nosec


def test_note_symbol_is_part_of_the_mapping():
    assert NOTE_TAG_SYMBOL in TAG_TYPES  # nosec


def test_render_legend_takes_a_custom_header():
    rendered = render_legend("Key")
    assert rendered.startswith("Key\n\n")  # nosec
    assert rendered.endswith("& - Notes\n")  # nosec


# --- the MCP docs quote exact tool counts; keep them true (#52) --------------


def test_mcp_doc_tool_counts_match_the_server():
    """``docs/mcp-server.md`` states tool counts; assert they are still right.

    Adding ``get_tag_types`` silently falsified three numbers in a doc that had
    merged the day before (#85). Counting them here means the next tool added
    fails this test instead of quietly making the documentation wrong.
    """
    from campaign_logger.mcp_server import create_mcp_server

    doc = (Path(__file__).parent.parent / "docs" / "mcp-server.md").read_text(encoding="utf-8")

    read_only = len(create_mcp_server(read_only=True)._tool_manager._tools)
    read_write = len(create_mcp_server(read_only=False)._tool_manager._tools)

    assert re.search(rf"read-only\s+— {read_only} tools", doc), f"doc does not say {read_only} read-only tools"
    assert re.search(rf"read\+write — {read_write} tools", doc), f"doc does not say {read_write} read+write tools"
    assert f"The {read_only} tools available in read-only mode" in doc

    # Every tool the read-only server registers must appear in the doc's table.
    for name in create_mcp_server(read_only=True)._tool_manager._tools:
        assert f"`{name}`" in doc, f"read-only tool {name} is undocumented"
