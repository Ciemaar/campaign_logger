"""Split a live campaign into flat text files suitable for RAG ingestion.

The campaign is fetched through :class:`~campaign_logger.api.LoggerClient`, so this
module consumes the snake_case model objects from :mod:`campaign_logger.models`
(``raw_public``, ``raw_text``, ``tag_symbol``, ``tag_value``) rather than the
camelCase keys of a hand-exported dump.  Every one of those fields is
``str | None``, so nothing here assumes a string is present.

Three kinds of output are produced in ``output_dir``:

1. ``<campaign>.public.txt`` -- legend header plus every entry's ``raw_public`` body.
2. ``<campaign>.private.txt`` -- the same headings with the ``raw_text`` body.
3. ``<log title>.txt`` -- one file per log, each log entry's title then its text.

Everything here is read-only: only ``get_*`` methods of the client are called.

The writers are ported from ``rag.ipynb`` and are intended to stay byte-comparable
with it for the same campaign content.
"""

import re
from pathlib import Path

#: The symbol legend written at the top of both the public and the private file.
SYMBOL_LEGEND = """Prefixes

@ - Cast of Characters - People
^ - Organizations
# - Gazetteer - Locations
$ - Money
! - Quartermaster - Equipment, Gear, Weapons
% - Calendar
* - Loopy Planning - Plot
~ - Rules/Spells
§ - Sections
+ - Pluses
- - Minuses
& - Notes
"""

#: Matches pasted Python import lines and ``%autoreload`` magics inside notes.
#:
#: Ported verbatim from ``rag.ipynb``.  Note that it is both DOTALL and greedy, so it
#: removes everything from the first import-looking line to the body's last newline,
#: not just the import lines themselves.  That is the behaviour the existing
#: ``*.private.txt`` files were generated with, so it is kept as-is and made opt-out.
IMPORT_REGEX = re.compile(r"\n(\s*(import|from)|%.*autoreload).*\n", re.MULTILINE | re.DOTALL)

#: The tag symbol used for free-form notes, which are the ones holding pasted code.
NOTE_TAG_SYMBOL = "&"

#: Campaign Logger stores U+00A0 where the editor saw a plain space.
NON_BREAKING_SPACE = " "

#: Characters that are unsafe in a filename on at least one supported platform.
UNSAFE_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')

#: Device names Windows refuses to use as a filename, whatever the extension.
RESERVED_FILENAMES = frozenset(["CON", "PRN", "AUX", "NUL"] + [f"COM{i}" for i in range(1, 10)] + [f"LPT{i}" for i in range(1, 10)])

#: Longest filename stem we will emit, so a runaway title cannot break the filesystem.
MAX_FILENAME_STEM = 120

#: Stem used when a log has no usable title at all.
FALLBACK_LOG_STEM = "log"

#: Stem used when the campaign itself has no usable title.
FALLBACK_CAMPAIGN_STEM = "campaign"


def normalise_spaces(text):
    """Replace non-breaking spaces with ordinary spaces.

    Args:
        text: The body text to normalise; ``None`` is treated as empty.

    Returns:
        str: The text with every U+00A0 replaced by a plain space.
    """
    return (text or "").replace(NON_BREAKING_SPACE, " ")


def strip_code(text):
    """Remove pasted import lines and ``%autoreload`` magics from a note body.

    Args:
        text: The note body to clean; ``None`` is treated as empty.

    Returns:
        str: The body with import-looking lines collapsed to a single newline.
    """
    return IMPORT_REGEX.sub("\n", text or "", count=0)


def sanitise_filename(title, used=None, fallback=FALLBACK_LOG_STEM):
    """Turn a title into a filename stem that is safe on every platform.

    Unsafe characters become underscores, surrounding whitespace and trailing dots
    are dropped (Windows silently strips them), Windows device names are prefixed,
    an empty result falls back to ``fallback``, and a stem already in ``used`` gains
    a numeric suffix so two logs never overwrite each other.

    Args:
        title: The title, which may be ``None``, empty, or contain path separators.
        used: A mutable set of stems already taken; updated with the result.
        fallback: Stem to use when nothing usable survives sanitisation.

    Returns:
        str: A filename stem, without the ``.txt`` extension.
    """
    stem = UNSAFE_FILENAME_CHARS.sub("_", title or "").strip()
    stem = stem.rstrip(". ")[:MAX_FILENAME_STEM].rstrip(". ")
    if not stem:
        stem = fallback
    if stem.upper() in RESERVED_FILENAMES:
        stem = f"_{stem}"
    if used is None:
        return stem
    candidate = stem
    counter = 1
    while candidate.lower() in used:
        counter += 1
        candidate = f"{stem}-{counter}"
    used.add(candidate.lower())
    return candidate


def write_campaign_entries(entries, public_path, private_path, strip_code_from_notes=True):
    """Write the public and private text files for a campaign's entries.

    Both files open with :data:`SYMBOL_LEGEND`.  Every entry contributes its heading
    to *both* files even when both bodies are empty, which is what the notebook did
    and what keeps the two files aligned entry for entry.

    Args:
        entries: An iterable of :class:`~campaign_logger.models.CampaignEntry`.
        public_path: Where to write the public text.
        private_path: Where to write the private text.
        strip_code_from_notes: Strip import lines from ``&`` note bodies in the
            private file.

    Returns:
        list[Path]: The two paths written, public first.
    """
    with open(public_path, "wt", encoding="utf-8") as public, open(private_path, "wt", encoding="utf-8") as private:
        public.write(SYMBOL_LEGEND)
        private.write(SYMBOL_LEGEND)
        for entry in entries or []:
            heading = f'\n{entry.tag_symbol or ""}"{entry.tag_value or ""}"\n\n'
            public.write(heading)
            private.write(heading)
            private_text = normalise_spaces(entry.raw_text)
            if strip_code_from_notes and entry.tag_symbol == NOTE_TAG_SYMBOL:
                private_text = strip_code(private_text)
            private.write(private_text)
            public.write(normalise_spaces(entry.raw_public))
    return [Path(public_path), Path(private_path)]


def write_logs(logs_with_entries, output_dir):
    """Write one text file per log, named after the log's sanitised title.

    Args:
        logs_with_entries: An iterable of ``(log, entries)`` pairs, so the caller owns
            the fetching and this stays a pure writer.
        output_dir: Directory the log files are written into.

    Returns:
        list[Path]: The paths written, in the order given.
    """
    output_dir = Path(output_dir)
    written = []
    used = set()
    for log, entries in logs_with_entries:
        path = output_dir / f"{sanitise_filename(log.title, used)}.txt"
        with open(path, "wt", encoding="utf-8") as log_file:
            for entry in entries or []:
                log_file.write(entry.title or "")
                log_file.write(entry.raw_text or "")
                log_file.write("\n\n")
        written.append(path)
    return written


def split_campaign(client, campaign_id, output_dir=None, strip_code_from_notes=True):
    """Fetch a campaign and split it into public, private and per-log text files.

    Only ``get_*`` methods of the client are used, so this never writes to the server.

    Args:
        client: A :class:`~campaign_logger.api.LoggerClient`.
        campaign_id: The campaign to fetch.
        output_dir: Directory to write into; defaults to the current directory.
        strip_code_from_notes: Strip import lines from ``&`` note bodies in the
            private file.

    Returns:
        list[Path]: Every file written, public and private first.
    """
    output_dir = Path(output_dir) if output_dir is not None else Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)

    campaign = client.get_campaign(campaign_id)
    stem = sanitise_filename(campaign.title, fallback=FALLBACK_CAMPAIGN_STEM)

    written = write_campaign_entries(
        client.get_campaign_entries(campaign_id),
        output_dir / f"{stem}.public.txt",
        output_dir / f"{stem}.private.txt",
        strip_code_from_notes=strip_code_from_notes,
    )

    logs = [log for log in client.get_logs() if log.campaign_id == campaign_id]
    written.extend(write_logs(((log, client.get_log_entries(log.id)) for log in logs), output_dir))
    return written
