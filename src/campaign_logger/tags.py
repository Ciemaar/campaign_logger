"""The tag symbols Campaign Logger uses to type campaign entries.

The API has no entity, NPC or location model. A campaign entry (a "page") carries
a ``tag_symbol`` and a ``tag_value``, and the symbol is what says which kind of
thing the page describes: ``@`` for a person, ``#`` for a place, and so on. So
this mapping is effectively the type system for campaign content, and any
consumer that wants "all the NPCs" is really asking for the campaign entries
whose ``tag_symbol`` is ``@``.

It lived as a text blob inside the RAG exporter until something else needed it.
Here it is a mapping first, with the exporter's header rendered from it, so a
caller can classify entries without parsing prose.

The labels are Campaign Logger's own, kept verbatim -- "Gazetteer" and
"Quartermaster" are the application's words for places and equipment, not ours
to improve.
"""

#: Tag symbol -> the label Campaign Logger gives that category.
#:
#: Order matters: :data:`SYMBOL_LEGEND` is rendered from it, and that header is
#: byte-compared against the exporter's historical output.
TAG_TYPES: dict[str, str] = {
    "@": "Cast of Characters - People",
    "^": "Organizations",
    "#": "Gazetteer - Locations",
    "$": "Money",
    "!": "Quartermaster - Equipment, Gear, Weapons",
    "%": "Calendar",
    "*": "Loopy Planning - Plot",
    "~": "Rules/Spells",
    "§": "Sections",
    "+": "Pluses",
    "-": "Minuses",
    "&": "Notes",
}

#: A short, machine-friendly name per symbol, for consumers that would rather
#: match on ``"people"`` than on ``"Cast of Characters - People"``. These are
#: ours, not Campaign Logger's, so treat :data:`TAG_TYPES` as the authority on
#: what a symbol means.
TAG_NAMES: dict[str, str] = {
    "@": "people",
    "^": "organizations",
    "#": "locations",
    "$": "money",
    "!": "equipment",
    "%": "calendar",
    "*": "plot",
    "~": "rules",
    "§": "sections",
    "+": "pluses",
    "-": "minuses",
    "&": "notes",
}

#: The symbol for free-form notes, which is the one the exporter special-cases.
NOTE_TAG_SYMBOL = "&"


def render_legend(header: str = "Prefixes") -> str:
    """Render the legend block that heads an exported text file.

    Args:
        header: The first line of the block.

    Returns:
        str: ``header``, a blank line, then one ``symbol - label`` line per
        entry of :data:`TAG_TYPES`, each newline-terminated.
    """
    lines = [f"{symbol} - {label}" for symbol, label in TAG_TYPES.items()]
    return f"{header}\n\n" + "".join(f"{line}\n" for line in lines)


#: The legend as the exporter writes it. Rendered rather than written out, so
#: the mapping above stays the single definition.
SYMBOL_LEGEND: str = render_legend()


def tag_name(symbol: str | None) -> str | None:
    """The short name for a tag symbol, or None if it is unknown or absent.

    Unknown symbols return None rather than raising: the set is Campaign
    Logger's and may grow, and a consumer classifying entries should be able to
    skip what it does not recognise rather than crash on it.
    """
    if not symbol:
        return None
    return TAG_NAMES.get(symbol)
