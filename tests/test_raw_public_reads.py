"""Regression tests for bodies that live only in ``raw-public`` (#89, #98).

A campaign entry's text can arrive in ``raw-text`` or in ``raw-public``. #70 added
:attr:`CampaignEntry.text` to paper over that, then every display site kept
reading ``raw_text`` directly, so a page whose body is only in ``raw-public``:

* printed nothing at all from ``page get`` (#89), and
* **disappeared from listings**, because the listing derived its label from
  ``raw_text`` and skipped any row it could not label (#98).

The second is the worse one: the caller is not shown a blank row, it is told the
page does not exist. These tests exercise the display paths with real models,
which is the thing that was missing -- the suite used ``MagicMock`` stubs that
answered ``raw_text`` as readily as the real model would (#95).
"""

import ast
import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from campaign_logger.cli import main
from campaign_logger.models import UNTITLED_LABEL
from campaign_logger.models import CampaignEntry

SRC = Path(__file__).parent.parent / "src" / "campaign_logger"

#: A page as the server sends one whose body was only ever public.
PUBLIC_ONLY = CampaignEntry(
    id="p2",
    type="campaign-entries",
    raw_public="  A place with no tag value  ",
)
#: An ordinary page, for contrast.
TAGGED = CampaignEntry(id="p1", type="campaign-entries", tag_value="Alice", raw_text="An NPC")


def tool_text(result: Any) -> str:
    """The text of an MCP tool result's first content block.

    ``call_tool`` returns a union -- text, image, audio, a resource link or an
    input-required result -- so the attribute access has to be narrowed rather
    than assumed. Asserting the shape here says what this test requires and fails
    loudly if a tool ever answers with something else, which a ``type: ignore``
    would hide.
    """
    content = getattr(result, "content", None)
    assert content, f"tool returned no content: {result!r}"
    text = getattr(content[0], "text", None)
    assert isinstance(text, str), f"first content block is not text: {content[0]!r}"
    return text


@pytest.fixture
def cli(monkeypatch, mocker):
    """A CLI runner wired to a mocked logger client, with credentials present."""
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    monkeypatch.delenv("CL_DEFAULT_CAMPAIGN_ID", raising=False)
    client = MagicMock()
    mocker.patch("campaign_logger.cli.LoggerClient", return_value=client)
    return CliRunner(), client


# --- #89: the body must be printed --------------------------------------------


def test_page_get_prints_a_body_that_is_only_public(cli):
    """``page get`` printed an empty line for these pages before this fix."""
    runner, client = cli
    client.get_campaign_entry.return_value = PUBLIC_ONLY

    result = runner.invoke(main, ["logger", "page", "get", "p2", "--raw"])

    assert result.exit_code == 0
    assert "A place with no tag value" in result.output


def test_page_get_still_prefers_raw_text_when_both_are_present(cli):
    """The fallback must not override a page that does have ``raw-text``."""
    runner, client = cli
    client.get_campaign_entry.return_value = CampaignEntry(
        id="p3", type="campaign-entries", raw_text="the private body", raw_public="the public body"
    )

    result = runner.invoke(main, ["logger", "page", "get", "p3", "--raw"])

    assert "the private body" in result.output
    assert "the public body" not in result.output


# --- #98: the row must exist ---------------------------------------------------


def test_page_list_includes_a_page_whose_body_is_only_public(cli):
    """The page was absent from this listing entirely, not merely unlabelled."""
    runner, client = cli
    client.get_campaign_entries.return_value = [TAGGED, PUBLIC_ONLY]

    result = runner.invoke(main, ["logger", "page", "list"])

    assert "p1: Alice" in result.output
    assert "p2: A place with no tag value" in result.output


def test_page_list_lists_a_page_with_nothing_to_label_it(cli):
    """A page with no tag value and no body at all still has an id worth showing."""
    runner, client = cli
    client.get_campaign_entries.return_value = [CampaignEntry(id="p9", type="campaign-entries")]

    result = runner.invoke(main, ["logger", "page", "list"])

    assert f"p9: {UNTITLED_LABEL}" in result.output


def test_mcp_listing_includes_a_page_whose_body_is_only_public(mocker):
    """The MCP server told the assistant the page did not exist."""
    mocker.patch("campaign_logger.mcp_server.load_config")
    mocker.patch.dict(
        "os.environ",
        {"CL_LOGGER_CLIENT_ID": "id", "CL_LOGGER_CLIENT_SECRET": "secret"},
        clear=True,
    )
    from campaign_logger.mcp_server import create_mcp_server

    client = MagicMock()
    mocker.patch("campaign_logger.mcp_server.LoggerClient", return_value=client)
    client.get_campaign_entries.return_value = [TAGGED, PUBLIC_ONLY]

    server = create_mcp_server(read_only=True)
    out = tool_text(asyncio.run(server.call_tool("list_campaign_entries", {})))

    assert "p1: Alice" in out
    assert "p2: A place with no tag value" in out


# --- the structural guard that would have prevented all of the above -----------


def _display_reads_of_raw_text(path):
    """Every ``x.raw_text`` that is *read* rather than assigned, in ``path``.

    Assignments are legitimate -- ``CampaignEntry.text`` has no setter, so an
    update has to write ``raw_text`` -- so only loads are reported.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    targets = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    targets.add(id(target))
    return [
        node.lineno for node in ast.walk(tree) if isinstance(node, ast.Attribute) and node.attr == "raw_text" and id(node) not in targets
    ]


@pytest.mark.parametrize("module", ["cli.py", "mcp_server.py"])
def test_display_code_never_reads_raw_text_directly(module):
    """Reading ``raw_text`` for display is the bug itself, so forbid it outright.

    #89 was one missed read, and it was missed three times over in the same file.
    A rule is what stops the fourth: the display layer goes through
    :attr:`BaseEntity.text`, which knows about the fallback, and only the update
    commands touch ``raw_text`` -- as assignments, which this ignores.
    """
    offenders = _display_reads_of_raw_text(SRC / module)
    assert not offenders, f"{module} reads .raw_text for display at lines {offenders}; use .text instead"
