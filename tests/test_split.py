"""Tests for splitting a live campaign into public/private and per-log text files (issue #74).

Nothing here touches the network: the client is either mocked at the HTTP layer with
``requests_mock`` and realistic kebab-case JSON:API payloads from ``wire``, or replaced
by a recording stub that also proves the command never writes to the server.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests_mock
import wire
from click.testing import CliRunner

from campaign_logger.api import LoggerClient
from campaign_logger.cli import main
from campaign_logger.models import CampaignEntry
from campaign_logger.models import Log
from campaign_logger.models import LogEntry
from campaign_logger.split import FALLBACK_CAMPAIGN_STEM
from campaign_logger.split import FALLBACK_LOG_STEM
from campaign_logger.split import SYMBOL_LEGEND
from campaign_logger.split import normalise_spaces
from campaign_logger.split import sanitise_filename
from campaign_logger.split import split_campaign
from campaign_logger.split import strip_code
from campaign_logger.split import write_campaign_entries
from campaign_logger.split import write_logs

BASE_URL = "https://logger-staging.campaign-logger.com"

NBSP = "\u00a0"

NOTE_WITH_CODE = "\nSome prose.\nimport dill\nfrom model import get_character\n%autoreload 2\nMore prose.\n"

#: Every mutating client method, so a test can assert the splitter called none of them.
WRITE_METHODS = [name for name in dir(LoggerClient) if name.startswith(("create_", "update_", "delete_"))]


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def client():
    return LoggerClient(base_url=BASE_URL, client_id="test_id", client_secret="test_secret")


def entry(**attrs):
    """A campaign entry model, built from field names rather than the wire aliases."""
    return CampaignEntry(id=attrs.pop("id", "ce1"), type="campaign-entries", **attrs)


def log(**attrs):
    """A log model, built from field names rather than the wire aliases."""
    return Log(id=attrs.pop("id", "l1"), type="logs", **attrs)


def log_entry(**attrs):
    """A log entry model, built from field names rather than the wire aliases."""
    return LogEntry(id=attrs.pop("id", "le1"), type="log-entries", **attrs)


def register_campaign(mocker_obj, entries=(), logs=(), log_entries=(), title="Test Campaign"):
    """Wire up the four read endpoints ``split_campaign`` calls."""
    mocker_obj.get(f"{BASE_URL}/campaigns/c1", json=wire.document("campaigns", "c1", title=title))
    mocker_obj.get(f"{BASE_URL}/campaign-entries", json=wire.collection("campaign-entries", *entries))
    mocker_obj.get(f"{BASE_URL}/logs", json=wire.collection("logs", *logs))
    mocker_obj.get(f"{BASE_URL}/log-entries", json=wire.collection("log-entries", *log_entries))


def campaign_fixture_payloads():
    """The realistic wire payloads for a campaign exercising every writer branch."""
    entries = [
        (
            "ce1",
            {
                "tag-symbol": "@",
                "tag-value": "Alice",
                "raw-text": "Alice is a spy.",
                "raw-public": "Alice is a merchant.",
                "campaign-id": "c1",
            },
        ),
        ("ce2", {"tag-symbol": "#", "tag-value": "Vault", "raw-text": "Under the keep.", "raw-public": "", "campaign-id": "c1"}),
        ("ce3", {"tag-symbol": "$", "tag-value": "Purse", "raw-text": "", "raw-public": "", "campaign-id": "c1"}),
        ("ce4", {"tag-symbol": "&", "tag-value": "Scratch", "raw-text": NOTE_WITH_CODE, "raw-public": "", "campaign-id": "c1"}),
        ("ce5", {"tag-symbol": "!", "tag-value": "Sword", "raw-text": f"a{NBSP}blade", "raw-public": f"a{NBSP}sword", "campaign-id": "c1"}),
        ("ce6", {"tag-symbol": "^", "tag-value": "Elsewhere", "raw-text": "Another campaign.", "raw-public": "", "campaign-id": "c2"}),
    ]
    logs = [
        ("l1", {"title": "Session 1: The Road/Home", "campaign-id": "c1"}),
        ("l2", {"title": "", "campaign-id": "c1"}),
        ("l3", {"title": "Other Campaign Log", "campaign-id": "c2"}),
    ]
    log_entries = [
        ("le1", {"title": "Arrival", "raw-text": "\nThey arrive.", "log-id": "l1"}),
        ("le2", {"title": "Nameless", "raw-text": "\nNo title.", "log-id": "l2"}),
        ("le3", {"title": "Elsewhere", "raw-text": "\nNot ours.", "log-id": "l3"}),
    ]
    return entries, logs, log_entries


def run_split(client, tmp_path, **kwargs):
    """Run ``split_campaign`` against the standard fixture campaign and read it back."""
    entries, logs, log_entries = campaign_fixture_payloads()
    with requests_mock.Mocker() as m:
        register_campaign(m, entries, logs, log_entries)
        written = split_campaign(client, "c1", output_dir=tmp_path, **kwargs)
    public = (tmp_path / "Test Campaign.public.txt").read_text(encoding="utf-8")
    private = (tmp_path / "Test Campaign.private.txt").read_text(encoding="utf-8")
    return public, private, written


# --- helpers ---------------------------------------------------------------


def test_normalise_spaces_replaces_nbsp():
    assert normalise_spaces(f"a{NBSP}b") == "a b"  # nosec
    assert normalise_spaces(None) == ""  # nosec


def test_strip_code_removes_imports_and_magics():
    cleaned = strip_code(NOTE_WITH_CODE)
    assert "import dill" not in cleaned  # nosec
    assert "from model import" not in cleaned  # nosec
    assert "autoreload" not in cleaned  # nosec
    assert "Some prose." in cleaned  # nosec
    assert strip_code(None) == ""  # nosec


def test_strip_code_is_greedy_to_the_last_newline():
    """The ported regex is DOTALL and greedy, so it also drops text after the imports.

    This is the notebook's behaviour, kept deliberately so the output stays
    byte-comparable with ``rag.ipynb``; it is why the stripping is opt-out.
    """
    assert strip_code("\nprose one\nimport dill\nprose two\n") == "\nprose one\n"  # nosec


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Session 1: The Road/Home", "Session 1_ The Road_Home"),
        ('a*b?c"d<e>f|g\\h', "a_b_c_d_e_f_g_h"),
        ("trailing dots...", "trailing dots"),
        ("  padded  ", "padded"),
        ("", FALLBACK_LOG_STEM),
        (None, FALLBACK_LOG_STEM),
        ("CON", "_CON"),
        ("lpt1", "_lpt1"),
    ],
)
def test_sanitise_filename(title, expected):
    assert sanitise_filename(title) == expected  # nosec


def test_sanitise_filename_truncates_long_titles():
    assert len(sanitise_filename("x" * 500)) == 120  # nosec


def test_sanitise_filename_deduplicates():
    used = set()
    assert sanitise_filename("Session", used) == "Session"  # nosec
    assert sanitise_filename("Session", used) == "Session-2"  # nosec
    assert sanitise_filename("session", used) == "session-3"  # nosec


def test_sanitise_filename_takes_a_custom_fallback():
    assert sanitise_filename(None, fallback=FALLBACK_CAMPAIGN_STEM) == "campaign"  # nosec


# --- campaign entries ------------------------------------------------------


def test_legend_header_starts_both_files(client, tmp_path):
    public, private, _ = run_split(client, tmp_path)
    assert public.startswith(SYMBOL_LEGEND)  # nosec
    assert private.startswith(SYMBOL_LEGEND)  # nosec
    assert "& - Notes" in SYMBOL_LEGEND  # nosec


def test_entry_with_both_bodies(client, tmp_path):
    public, private, _ = run_split(client, tmp_path)
    assert '\n@"Alice"\n\nAlice is a merchant.' in public  # nosec
    assert '\n@"Alice"\n\nAlice is a spy.' in private  # nosec


def test_entry_with_only_a_private_body_still_gets_a_public_heading(client, tmp_path):
    public, private, _ = run_split(client, tmp_path)
    assert '\n#"Vault"\n\nUnder the keep.' in private  # nosec
    assert '\n#"Vault"\n\n' in public  # nosec
    assert "Under the keep." not in public  # nosec


def test_empty_entry_still_writes_heading_to_both(client, tmp_path):
    public, private, _ = run_split(client, tmp_path)
    assert '\n$"Purse"\n\n' in public  # nosec
    assert '\n$"Purse"\n\n' in private  # nosec


def test_note_entry_has_code_stripped_by_default(client, tmp_path):
    _, private, _ = run_split(client, tmp_path)
    assert '\n&"Scratch"\n\n' in private  # nosec
    assert "import dill" not in private  # nosec
    assert "%autoreload" not in private  # nosec
    assert "Some prose." in private  # nosec


def test_note_entry_keeps_code_when_flag_disabled(client, tmp_path):
    _, private, _ = run_split(client, tmp_path, strip_code_from_notes=False)
    assert "import dill" in private  # nosec
    assert "%autoreload 2" in private  # nosec


def test_non_note_entries_are_never_code_stripped(tmp_path):
    entries = [entry(tag_symbol="@", tag_value="Coder", raw_text=NOTE_WITH_CODE, raw_public="")]
    write_campaign_entries(entries, tmp_path / "p.txt", tmp_path / "s.txt")
    assert "import dill" in (tmp_path / "s.txt").read_text(encoding="utf-8")  # nosec


def test_non_breaking_spaces_normalised_in_both_bodies(client, tmp_path):
    public, private, _ = run_split(client, tmp_path)
    assert "a sword" in public  # nosec
    assert "a blade" in private  # nosec
    assert NBSP not in public  # nosec
    assert NBSP not in private  # nosec


def test_none_valued_fields_do_not_crash(tmp_path):
    """Every model field the writers touch is ``str | None`` as of #70."""
    write_campaign_entries([entry()], tmp_path / "p.txt", tmp_path / "s.txt")
    assert '\n""\n\n' in (tmp_path / "p.txt").read_text(encoding="utf-8")  # nosec
    assert (tmp_path / "s.txt").read_text(encoding="utf-8") == SYMBOL_LEGEND + '\n""\n\n'  # nosec


def test_entries_are_filtered_to_the_requested_campaign(client, tmp_path):
    public, private, _ = run_split(client, tmp_path)
    assert "Another campaign." not in private  # nosec
    assert '\n^"Elsewhere"' not in public  # nosec


def test_public_only_entry_is_mirrored_into_the_private_body(client, tmp_path):
    """The client back-fills ``raw_text`` from ``raw_public`` when the former is empty.

    This is ``_parse_campaign_entry``'s behaviour, not the splitter's, and it is a
    real difference from the dump: a page whose body lives only in ``raw-public``
    appears in both files rather than the public one alone.
    """
    payload = [("ce1", {"tag-symbol": "^", "tag-value": "Guild", "raw-text": "", "raw-public": "A guild of thieves.", "campaign-id": "c1"})]
    with requests_mock.Mocker() as m:
        register_campaign(m, payload)
        split_campaign(client, "c1", output_dir=tmp_path)
    public = (tmp_path / "Test Campaign.public.txt").read_text(encoding="utf-8")
    private = (tmp_path / "Test Campaign.private.txt").read_text(encoding="utf-8")
    assert '\n^"Guild"\n\nA guild of thieves.' in public  # nosec
    assert '\n^"Guild"\n\nA guild of thieves.' in private  # nosec


# --- logs ------------------------------------------------------------------


def test_log_files_are_named_after_sanitised_titles(client, tmp_path):
    _, _, written = run_split(client, tmp_path)
    assert sorted(p.name for p in written) == [  # nosec
        "Session 1_ The Road_Home.txt",
        "Test Campaign.private.txt",
        "Test Campaign.public.txt",
        "log.txt",
    ]


def test_log_file_contents(client, tmp_path):
    run_split(client, tmp_path)
    assert (tmp_path / "Session 1_ The Road_Home.txt").read_text(encoding="utf-8") == "Arrival\nThey arrive.\n\n"  # nosec


def test_logs_are_filtered_to_the_requested_campaign(client, tmp_path):
    _, _, written = run_split(client, tmp_path)
    assert not (tmp_path / "Other Campaign Log.txt").exists()  # nosec
    assert len(written) == 4  # nosec


def test_duplicate_log_titles_get_distinct_files(tmp_path):
    logs = [(log(id="l1", title="Same"), [log_entry(title="A", raw_text="1")]), (log(id="l2", title="Same"), [])]
    written = write_logs(logs, tmp_path)
    assert [p.name for p in written] == ["Same.txt", "Same-2.txt"]  # nosec
    assert (tmp_path / "Same-2.txt").read_text(encoding="utf-8") == ""  # nosec


def test_log_entry_with_none_fields_does_not_crash(tmp_path):
    write_logs([(log(title="L"), [log_entry()])], tmp_path)
    assert (tmp_path / "L.txt").read_text(encoding="utf-8") == "\n\n"  # nosec


# --- whole-campaign behaviour ----------------------------------------------


def test_campaign_with_no_entries_and_no_logs(client, tmp_path):
    with requests_mock.Mocker() as m:
        register_campaign(m)
        written = split_campaign(client, "c1", output_dir=tmp_path)
    assert [p.name for p in written] == ["Test Campaign.public.txt", "Test Campaign.private.txt"]  # nosec
    assert written[0].read_text(encoding="utf-8") == SYMBOL_LEGEND  # nosec
    assert written[1].read_text(encoding="utf-8") == SYMBOL_LEGEND  # nosec


def test_untitled_campaign_falls_back_to_a_safe_stem(client, tmp_path):
    with requests_mock.Mocker() as m:
        register_campaign(m, title="")
        written = split_campaign(client, "c1", output_dir=tmp_path)
    assert [p.name for p in written] == ["campaign.public.txt", "campaign.private.txt"]  # nosec


def test_campaign_title_is_sanitised_for_the_output_filenames(client, tmp_path):
    with requests_mock.Mocker() as m:
        register_campaign(m, title="Cock a/Knee: Act 1")
        written = split_campaign(client, "c1", output_dir=tmp_path)
    assert written[0].name == "Cock a_Knee_ Act 1.public.txt"  # nosec


def test_output_dir_is_created_when_missing(client, tmp_path):
    out = tmp_path / "nested" / "out"
    _, _, written = run_split(client, out)
    assert out.is_dir()  # nosec
    assert all(p.parent == out for p in written)  # nosec


def test_output_dir_defaults_to_the_current_directory(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with requests_mock.Mocker() as m:
        register_campaign(m)
        written = split_campaign(client, "c1")
    assert all(p.parent == Path.cwd() for p in written)  # nosec


def test_split_is_read_only(tmp_path):
    """No POST, PATCH or DELETE may reach the server on any code path."""
    stub = MagicMock()
    stub.get_campaign.return_value = MagicMock(title="Read Only")
    stub.get_campaign_entries.return_value = [entry(tag_symbol="@", tag_value="A", raw_text="x", raw_public="y")]
    stub.get_logs.return_value = [log(title="L", campaign_id="c1")]
    stub.get_log_entries.return_value = [log_entry(title="T", raw_text="t", log_id="l1")]

    split_campaign(stub, "c1", output_dir=tmp_path)

    called = {name for name in WRITE_METHODS if getattr(stub, name).called}
    assert called == set()  # nosec
    assert stub.get_campaign_entries.call_args.args == ("c1",)  # nosec
    assert stub.get_log_entries.call_args.args == ("l1",)  # nosec


# --- CLI -------------------------------------------------------------------


@pytest.fixture
def cli_client(mocker, tmp_path):
    """A mocked LoggerClient wired into the CLI, returning one entry and one log."""
    stub = MagicMock()
    stub.get_campaign.return_value = MagicMock(title="CLI Campaign")
    stub.get_campaign_entries.return_value = [
        entry(tag_symbol="@", tag_value="Alice", raw_text="private body", raw_public="public body"),
        entry(id="ce2", tag_symbol="&", tag_value="Scratch", raw_text=NOTE_WITH_CODE, raw_public=""),
    ]
    stub.get_logs.return_value = [log(title="Session 1: The Road/Home", campaign_id="c1")]
    stub.get_log_entries.return_value = [log_entry(title="Arrival", raw_text="\nThey arrive.", log_id="l1")]
    mocker.patch("campaign_logger.cli.LoggerClient", return_value=stub)
    return stub


def test_cli_split(runner, cli_client, tmp_path, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "campaign", "split", "c1", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0  # nosec
    assert "CLI Campaign.public.txt" in result.output  # nosec
    cli_client.get_campaign.assert_called_once_with("c1")
    private = (tmp_path / "CLI Campaign.private.txt").read_text(encoding="utf-8")
    assert private.endswith('\n@"Alice"\n\nprivate body\n&"Scratch"\n\n\nSome prose.\n')  # nosec
    assert "import dill" not in private  # nosec
    assert (tmp_path / "CLI Campaign.public.txt").read_text(encoding="utf-8").endswith('\n@"Alice"\n\npublic body\n&"Scratch"\n\n')  # nosec
    assert (tmp_path / "Session 1_ The Road_Home.txt").is_file()  # nosec


def test_cli_split_defaults_to_the_current_directory(runner, cli_client, tmp_path, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["logger", "campaign", "split", "c1"])
    assert result.exit_code == 0  # nosec
    assert (tmp_path / "CLI Campaign.public.txt").is_file()  # nosec


def test_cli_split_no_strip_flag(runner, cli_client, tmp_path, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    result = runner.invoke(main, ["logger", "campaign", "split", "c1", "--output-dir", str(tmp_path), "--no-strip-code-from-notes"])
    assert result.exit_code == 0  # nosec
    assert "import dill" in (tmp_path / "CLI Campaign.private.txt").read_text(encoding="utf-8")  # nosec


def test_cli_split_reports_api_errors(runner, cli_client, tmp_path, monkeypatch):
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    cli_client.get_campaign.side_effect = json.JSONDecodeError("boom", "", 0)
    result = runner.invoke(main, ["logger", "campaign", "split", "c1", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0  # nosec
    assert "Error:" in result.output  # nosec


def test_cli_split_needs_credentials(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("CL_LOGGER_CLIENT_ID", raising=False)
    monkeypatch.delenv("CL_LOGGER_CLIENT_SECRET", raising=False)
    result = runner.invoke(main, ["logger", "campaign", "split", "c1", "--output-dir", str(tmp_path)])
    assert result.exit_code == 1  # nosec
    assert "Error: Missing client ID or secret" in result.output  # nosec


def test_log_cannot_overwrite_the_campaign_output_files(tmp_path):
    """A log titled like the campaign's own output must not clobber it.

    The campaign writes <stem>.public.txt and <stem>.private.txt first; the log
    filenames are deduped against a fresh set, so without seeding that set a log
    titled "<stem>.public" silently overwrote the public file.
    """
    from types import SimpleNamespace as NS

    class Client:
        def get_campaign(self, campaign_id):
            return NS(title="Camp")

        def get_campaign_entries(self, campaign_id):
            return [NS(tag_symbol="@", tag_value="Bob", raw_text="private body", raw_public="public body")]

        def get_logs(self):
            return [NS(id="l1", title="Camp.public", campaign_id="c1"), NS(id="l2", title="Camp.private", campaign_id="c1")]

        def get_log_entries(self, log_id):
            return [NS(title="T", raw_text="LOG BODY")]

    written = split_campaign(Client(), "c1", output_dir=tmp_path)

    assert len({path.name for path in written}) == len(written)  # nosec  no two outputs share a name
    assert "LOG BODY" not in (tmp_path / "Camp.public.txt").read_text()  # nosec
    assert "public body" in (tmp_path / "Camp.public.txt").read_text()  # nosec
    assert "LOG BODY" not in (tmp_path / "Camp.private.txt").read_text()  # nosec
