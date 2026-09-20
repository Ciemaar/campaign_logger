"""The tag symbols are the type system for campaign content, so pin them.

A consumer asking for "the NPCs" is really asking for campaign entries whose
``tag_symbol`` is ``@``. That makes this mapping an interface, not a detail.
"""

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
