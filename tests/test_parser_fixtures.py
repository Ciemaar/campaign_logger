import json
import os

from campaign_logger.api import LoggerClient


def test_parse_log_entry_from_fixture():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "log_entry_kebab.json")
    with open(fixture_path, "r") as f:
        data = json.load(f)["data"]

    client = LoggerClient()
    entry = client._parse_log_entry(data)

    assert entry.id == "e2-kebab"
    assert entry.log_id == "l1"
    assert entry.raw_text == "Log text via kebab"


def test_parse_campaign_entry_from_fixture():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "campaign_entry_kebab.json")
    with open(fixture_path, "r") as f:
        data = json.load(f)["data"]

    client = LoggerClient()
    entry = client._parse_campaign_entry(data)

    assert entry.id == "ce2-kebab"
    assert entry.campaign_id == "c1"
    assert entry.raw_text == "@Test Page\nContent via raw-public"
