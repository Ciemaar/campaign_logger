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
    assert entry.raw_text == "Content via raw-public"


def test_parse_log_from_fixture():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "log_kebab.json")
    with open(fixture_path, "r") as f:
        data = json.load(f)["data"]

    client = LoggerClient()
    log_obj = client._parse_log(data)

    assert log_obj.id == "log1-kebab"
    assert log_obj.campaign_id == "c1"
    assert log_obj.title == "Log via kebab"


def test_parse_campaign_from_fixture():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "campaign_kebab.json")
    with open(fixture_path, "r") as f:
        data = json.load(f)["data"]

    client = LoggerClient()
    campaign_obj = client._parse_campaign(data)

    assert campaign_obj.id == "c1-kebab"
    assert campaign_obj.title == "Campaign via kebab"


def test_parse_log_entry_from_fixture_title_fallback():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "log_entry_title.json")
    with open(fixture_path, "r") as f:
        data = json.load(f)["data"]

    client = LoggerClient()
    entry = client._parse_log_entry(data)

    assert entry.id == "le-title"
    assert entry.log_id == "l1"
    assert entry.raw_text == ""


def test_parse_campaign_entry_from_fixture_tag_value_fallback():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "campaign_entry_title.json")
    with open(fixture_path, "r") as f:
        data = json.load(f)["data"]

    client = LoggerClient()
    entry = client._parse_campaign_entry(data)

    assert entry.id == "ce-title"
    assert entry.campaign_id == "c1"
    assert entry.raw_text == ""


def test_parse_log_entry_relationships():
    payload = {
        "attributes": {
            "raw-text": "Some text",
        },
        "relationships": {"log": {"data": {"type": "logs", "id": "rel_log_id"}}},
        "type": "log-entries",
        "id": "e_id",
    }

    client = LoggerClient()
    entry = client._parse_log_entry(payload)
    assert entry.log_id == "rel_log_id"


def test_parse_campaign_entry_relationships():
    payload = {
        "attributes": {
            "raw-text": "Some text",
        },
        "relationships": {"campaign": {"data": {"type": "campaigns", "id": "rel_campaign_id"}}},
        "type": "campaign-entries",
        "id": "ce_id",
    }

    client = LoggerClient()
    entry = client._parse_campaign_entry(payload)
    assert entry.campaign_id == "rel_campaign_id"


def test_parse_log_relationships():
    payload = {
        "attributes": {
            "title": "Some text",
        },
        "relationships": {"campaign": {"data": {"type": "campaigns", "id": "rel_campaign_id"}}},
        "type": "logs",
        "id": "l_id",
    }

    client = LoggerClient()
    log_obj = client._parse_log(payload)
    assert log_obj.campaign_id == "rel_campaign_id"
