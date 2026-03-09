import secrets

import pytest
import requests_mock

from campaign_logger.api import LoggerClient

BASE_URL = "https://logger.campaign-logger.com"


@pytest.fixture
def client():
    return LoggerClient(base_url=BASE_URL, token=secrets.token_hex(16))


def test_get_campaigns(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaigns", json={"data": [{"id": "c1", "type": "campaigns"}]})
        result = client.get_campaigns()
        assert len(result.data) == 1  # nosec
        assert result.data[0].id == "c1"  # nosec


def test_get_campaign(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaigns/c1", json={"data": {"id": "c1", "type": "campaigns"}})
        result = client.get_campaign("c1")
        assert result.data.id == "c1"  # nosec


def test_create_campaign(client):
    with requests_mock.Mocker() as m:
        m.post(
            f"{BASE_URL}/campaigns",
            json={"data": {"id": "c1", "type": "campaigns", "attributes": {"title": "My Campaign"}}},
        )
        result = client.create_campaign("My Campaign", "A description")
        assert result.data.id == "c1"  # nosec


def test_update_campaign(client):
    with requests_mock.Mocker() as m:
        m.patch(f"{BASE_URL}/campaigns/c1", json={"data": {"id": "c1", "type": "campaigns"}})
        result = client.update_campaign("c1", title="New Title")
        assert result.data.id == "c1"  # nosec


def test_delete_campaign(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/campaigns/c1", status_code=204)
        client.delete_campaign("c1")
        assert m.called  # nosec


def test_get_logs(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/logs", json={"data": [{"id": "l1", "type": "logs"}]})
        result = client.get_logs()
        assert len(result.data) == 1  # nosec
        assert result.data[0].id == "l1"  # nosec


def test_create_log(client):
    with requests_mock.Mocker() as m:
        m.post(
            f"{BASE_URL}/logs",
            json={"data": {"id": "l1", "type": "logs", "attributes": {"title": "My Log"}}},
        )
        result = client.create_log("c1", "My Log", "Log desc")
        assert result.data.id == "l1"  # nosec


def test_update_log(client):
    with requests_mock.Mocker() as m:
        m.patch(f"{BASE_URL}/logs/l1", json={"data": {"id": "l1", "type": "logs"}})
        result = client.update_log("l1", title="New Title")
        assert result.data.id == "l1"  # nosec


def test_delete_log(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/logs/l1", status_code=204)
        client.delete_log("l1")
        assert m.called  # nosec


def test_get_log_entries(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/log-entries", json={"data": [{"id": "le1", "type": "log-entries"}]})
        result = client.get_log_entries()
        assert len(result.data) == 1  # nosec
        assert result.data[0].id == "le1"  # nosec


def test_create_log_entry(client):
    with requests_mock.Mocker() as m:
        m.post(
            f"{BASE_URL}/log-entries",
            json={"data": {"id": "le1", "type": "log-entries"}},
        )
        result = client.create_log_entry("l1", "A log entry text")
        assert result.data.id == "le1"  # nosec


def test_update_log_entry(client):
    with requests_mock.Mocker() as m:
        m.patch(f"{BASE_URL}/log-entries/le1", json={"data": {"id": "le1", "type": "log-entries"}})
        result = client.update_log_entry("le1", "New text")
        assert result.data.id == "le1"  # nosec


def test_delete_log_entry(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/log-entries/le1", status_code=204)
        client.delete_log_entry("le1")
        assert m.called  # nosec


def test_get_campaign_entries(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaign-entries", json={"data": [{"id": "ce1", "type": "campaign-entries"}]})
        result = client.get_campaign_entries()
        assert len(result.data) == 1  # nosec
        assert result.data[0].id == "ce1"  # nosec


def test_create_campaign_entry(client):
    with requests_mock.Mocker() as m:
        m.post(
            f"{BASE_URL}/campaign-entries",
            json={"data": {"id": "ce1", "type": "campaign-entries"}},
        )
        result = client.create_campaign_entry("c1", "A page text")
        assert result.data.id == "ce1"  # nosec


def test_update_campaign_entry(client):
    with requests_mock.Mocker() as m:
        m.patch(f"{BASE_URL}/campaign-entries/ce1", json={"data": {"id": "ce1", "type": "campaign-entries"}})
        result = client.update_campaign_entry("ce1", "New text")
        assert result.data.id == "ce1"  # nosec


def test_delete_campaign_entry(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/campaign-entries/ce1", status_code=204)
        client.delete_campaign_entry("ce1")
        assert m.called  # nosec
