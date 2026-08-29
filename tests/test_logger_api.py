import pytest
import requests_mock

from campaign_logger.api import LoggerClient

BASE_URL = "https://logger.campaign-logger.com"


@pytest.fixture
def client():
    return LoggerClient(base_url=BASE_URL, client_id="test_id", client_secret="test_secret")


def test_get_campaigns(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaigns", json={"data": [{"id": "c1", "type": "campaigns"}]})
        result = client.get_campaigns()
        assert len(result) == 1  # nosec
        assert result[0].id == "c1"  # nosec


def test_get_campaign(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaigns/c1", json={"data": {"id": "c1", "type": "campaigns"}})
        result = client.get_campaign("c1")
        assert result.id == "c1"  # nosec


def test_create_campaign(client):
    with requests_mock.Mocker() as m:
        m.post(
            f"{BASE_URL}/campaigns",
            json={"data": {"id": "c1", "type": "campaigns", "attributes": {"title": "My Campaign"}}},
        )
        result = client.create_campaign("My Campaign", "A description")
        assert result.id == "c1"  # nosec


def test_update_campaign(client):
    with requests_mock.Mocker() as m:
        m.patch(f"{BASE_URL}/campaigns/c1", json={"data": {"id": "c1", "type": "campaigns"}})
        result = client.update_campaign("c1", title="New Title")
        assert result.id == "c1"  # nosec

        result2 = client.update_campaign("c1", description="New Desc")
        assert result2.id == "c1"  # nosec

        result3 = client.update_campaign("c1")
        assert result3.id == "c1"  # nosec


def test_delete_campaign(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/campaigns/c1", status_code=204)
        client.delete_campaign("c1")
        assert m.called  # nosec


def test_get_logs(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/logs", json={"data": [{"id": "l1", "type": "logs"}]})
        result = client.get_logs()
        assert len(result) == 1  # nosec
        assert result[0].id == "l1"  # nosec


def test_create_log(client):
    with requests_mock.Mocker() as m:
        m.post(
            f"{BASE_URL}/logs",
            json={"data": {"id": "l1", "type": "logs", "attributes": {"title": "My Log"}}},
        )
        result = client.create_log("c1", "My Log", "Log desc")
        assert result.id == "l1"  # nosec


def test_update_log(client):
    with requests_mock.Mocker() as m:
        m.patch(f"{BASE_URL}/logs/l1", json={"data": {"id": "l1", "type": "logs"}})
        result = client.update_log("l1", title="New Title")
        assert result.id == "l1"  # nosec

        result2 = client.update_log("l1", description="New Desc")
        assert result2.id == "l1"  # nosec

        result3 = client.update_log("l1")
        assert result3.id == "l1"  # nosec


def test_delete_log(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/logs/l1", status_code=204)
        client.delete_log("l1")
        assert m.called  # nosec


def test_get_log_entries(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/log-entries", json={"data": [{"id": "le1", "type": "log-entries"}]})
        result = client.get_log_entries()
        assert len(result) == 1  # nosec
        assert result[0].id == "le1"  # nosec


def test_create_log_entry(client):
    with requests_mock.Mocker() as m:
        m.post(
            f"{BASE_URL}/log-entries",
            json={"data": {"id": "le1", "type": "log-entries"}},
        )
        result = client.create_log_entry("l1", "A log entry text")
        assert result.id == "le1"  # nosec


def test_update_log_entry(client):
    with requests_mock.Mocker() as m:
        m.patch(f"{BASE_URL}/log-entries/le1", json={"data": {"id": "le1", "type": "log-entries"}})
        result = client.update_log_entry("le1", "New text")
        assert result.id == "le1"  # nosec


def test_delete_log_entry(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/log-entries/le1", status_code=204)
        client.delete_log_entry("le1")
        assert m.called  # nosec


def test_get_campaign_entries(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaign-entries", json={"data": [{"id": "ce1", "type": "campaign-entries"}]})
        result = client.get_campaign_entries()
        assert len(result) == 1  # nosec
        assert result[0].id == "ce1"  # nosec


def test_create_campaign_entry(client):
    with requests_mock.Mocker() as m:
        m.post(
            f"{BASE_URL}/campaign-entries",
            json={"data": {"id": "ce1", "type": "campaign-entries"}},
        )
        result = client.create_campaign_entry("c1", "A page text")
        assert result.id == "ce1"  # nosec


def test_update_campaign_entry(client):
    with requests_mock.Mocker() as m:
        m.patch(f"{BASE_URL}/campaign-entries/ce1", json={"data": {"id": "ce1", "type": "campaign-entries"}})
        result = client.update_campaign_entry("ce1", "New text")
        assert result.id == "ce1"  # nosec


def test_delete_campaign_entry(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/campaign-entries/ce1", status_code=204)
        client.delete_campaign_entry("ce1")
        assert m.called  # nosec


def test_campaign_methods(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaigns/c1", json={"data": {"id": "c1", "type": "campaigns"}})
        campaign = client.get_campaign("c1")

        m.get(f"{BASE_URL}/logs", json={"data": [{"id": "l1", "type": "logs", "attributes": {"campaignId": "c1"}}]})
        logs = campaign.get_logs()
        assert len(logs) == 1  # nosec
        assert logs[0].id == "l1"  # nosec

        m.post(f"{BASE_URL}/logs", json={"data": {"id": "l2", "type": "logs", "attributes": {"campaignId": "c1"}}})
        new_log = campaign.create_log("Test Log")
        assert new_log.id == "l2"  # nosec

        m.get(
            f"{BASE_URL}/campaign-entries",
            json={"data": [{"id": "ce1", "type": "campaign-entries", "attributes": {"campaignId": "c1"}}]},
        )
        entries = campaign.get_entries()
        assert len(entries) == 1  # nosec

        m.post(
            f"{BASE_URL}/campaign-entries",
            json={"data": {"id": "ce2", "type": "campaign-entries", "attributes": {"campaignId": "c1"}}},
        )
        new_entry = campaign.create_entry("text")
        assert new_entry.id == "ce2"  # nosec

        m.patch(f"{BASE_URL}/campaigns/c1", json={"data": {"id": "c1", "type": "campaigns"}})
        campaign.title = "Updated"
        upd = campaign.save()
        assert upd.id == "c1"  # nosec

        m.delete(f"{BASE_URL}/campaigns/c1", status_code=204)
        campaign.delete()
        assert m.called  # nosec


def test_log_methods(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/logs/l1", json={"data": {"id": "l1", "type": "logs", "attributes": {"campaignId": "c1"}}})
        log_obj = client.get_log("l1")

        m.get(f"{BASE_URL}/log-entries", json={"data": [{"id": "le1", "type": "log-entries", "attributes": {"logId": "l1"}}]})
        entries = log_obj.get_entries()
        assert len(entries) == 1  # nosec

        m.post(f"{BASE_URL}/log-entries", json={"data": {"id": "le2", "type": "log-entries", "attributes": {"logId": "l1"}}})
        new_entry = log_obj.create_entry("text")
        assert new_entry.id == "le2"  # nosec

        m.patch(f"{BASE_URL}/logs/l1", json={"data": {"id": "l1", "type": "logs"}})
        log_obj.title = "Updated"
        upd = log_obj.save()
        assert upd.id == "l1"  # nosec

        m.delete(f"{BASE_URL}/logs/l1", status_code=204)
        log_obj.delete()
        assert m.called  # nosec


def test_log_entry_methods(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/log-entries/le1", json={"data": {"id": "le1", "type": "log-entries", "attributes": {"logId": "l1"}}})
        entry = client.get_log_entry("le1")

        m.patch(f"{BASE_URL}/log-entries/le1", json={"data": {"id": "le1", "type": "log-entries"}})
        entry.raw_text = "New Text"
        upd = entry.save()
        assert upd.id == "le1"  # nosec

        m.delete(f"{BASE_URL}/log-entries/le1", status_code=204)
        entry.delete()
        assert m.called  # nosec


def test_campaign_entry_methods(client):
    with requests_mock.Mocker() as m:
        m.get(
            f"{BASE_URL}/campaign-entries/ce1",
            json={"data": {"id": "ce1", "type": "campaign-entries", "attributes": {"campaignId": "c1"}}},
        )
        entry = client.get_campaign_entry("ce1")

        m.patch(f"{BASE_URL}/campaign-entries/ce1", json={"data": {"id": "ce1", "type": "campaign-entries"}})
        entry.raw_text = "New Text"
        upd = entry.save()
        assert upd.id == "ce1"  # nosec

        m.delete(f"{BASE_URL}/campaign-entries/ce1", status_code=204)
        entry.delete()
        assert m.called  # nosec


def test_get_campaigns_list_handling(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaigns/c1", json={"data": [{"id": "c1", "type": "campaigns"}]})
        try:
            client.get_campaign("c1")
        except ValueError as e:
            assert "Expected a single resource" in str(e)  # nosec

        m.post(f"{BASE_URL}/campaigns", json={"data": [{"id": "c1", "type": "campaigns"}]})
        try:
            client.create_campaign("Title")
        except ValueError:
            pass

        m.patch(f"{BASE_URL}/campaigns/c1", json={"data": [{"id": "c1", "type": "campaigns"}]})
        try:
            client.update_campaign("c1")
        except ValueError:
            pass


def test_get_logs_list_handling(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/logs/l1", json={"data": [{"id": "l1", "type": "logs"}]})
        try:
            client.get_log("l1")
        except ValueError:
            pass

        m.post(f"{BASE_URL}/logs", json={"data": [{"id": "l1", "type": "logs"}]})
        try:
            client.create_log("c1", "Title")
        except ValueError:
            pass

        m.patch(f"{BASE_URL}/logs/l1", json={"data": [{"id": "l1", "type": "logs"}]})
        try:
            client.update_log("l1")
        except ValueError:
            pass


def test_get_log_entries_list_handling(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/log-entries/e1", json={"data": [{"id": "e1", "type": "log-entries"}]})
        try:
            client.get_log_entry("e1")
        except ValueError:
            pass

        m.post(f"{BASE_URL}/log-entries", json={"data": [{"id": "e1", "type": "log-entries"}]})
        try:
            client.create_log_entry("l1", "text")
        except ValueError:
            pass

        m.patch(f"{BASE_URL}/log-entries/e1", json={"data": [{"id": "e1", "type": "log-entries"}]})
        try:
            client.update_log_entry("e1", "text")
        except ValueError:
            pass


def test_get_campaign_entries_list_handling(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaign-entries/ce1", json={"data": [{"id": "ce1", "type": "campaign-entries"}]})
        try:
            client.get_campaign_entry("ce1")
        except ValueError:
            pass

        m.post(f"{BASE_URL}/campaign-entries", json={"data": [{"id": "ce1", "type": "campaign-entries"}]})
        try:
            client.create_campaign_entry("c1", "text")
        except ValueError:
            pass

        m.patch(f"{BASE_URL}/campaign-entries/ce1", json={"data": [{"id": "ce1", "type": "campaign-entries"}]})
        try:
            client.update_campaign_entry("ce1", "text")
        except ValueError:
            pass


def test_kebab_case_parsing(client):
    with requests_mock.Mocker() as m:
        # Test Campaign Entry parsing with kebab-case and split properties
        m.get(
            f"{BASE_URL}/campaign-entries/ce_kebab",
            json={
                "data": {
                    "id": "ce_kebab",
                    "type": "campaign-entries",
                    "attributes": {
                        "campaign-id": "c1",
                        "raw-public": "This is public text",
                        "tag-symbol": "~",
                        "tag-value": "Test Page",
                    },
                }
            },
        )
        entry = client.get_campaign_entry("ce_kebab")
        assert entry.id == "ce_kebab"  # nosec
        assert entry.campaign_id == "c1"  # nosec
        assert entry.raw_text == "This is public text"  # nosec

        # Test Log Entry parsing with kebab-case
        m.get(
            f"{BASE_URL}/log-entries/le_kebab",
            json={
                "data": {
                    "id": "le_kebab",
                    "type": "log-entries",
                    "attributes": {
                        "log-id": "l1",
                        "raw-text": "Log text via kebab",
                    },
                }
            },
        )
        log_entry = client.get_log_entry("le_kebab")
        assert log_entry.id == "le_kebab"  # nosec
        assert log_entry.log_id == "l1"  # nosec
        assert log_entry.raw_text == "Log text via kebab"  # nosec


def test_get_log_entries_filter(client):
    with requests_mock.Mocker() as m:
        m.get(
            f"{BASE_URL}/log-entries",
            json={
                "data": [
                    {"id": "e1", "type": "log-entries", "attributes": {"logId": "l1"}},
                    {"id": "e2", "type": "log-entries", "attributes": {"logId": "l2"}},
                ]
            },
        )
        entries = client.get_log_entries(log_id="l1")
        assert len(entries) == 1
        assert entries[0].id == "e1"


def test_get_campaign_entries_filter(client):
    with requests_mock.Mocker() as m:
        m.get(
            f"{BASE_URL}/campaign-entries",
            json={
                "data": [
                    {"id": "ce1", "type": "campaign-entries", "attributes": {"campaignId": "c1"}},
                    {"id": "ce2", "type": "campaign-entries", "attributes": {"campaignId": "c2"}},
                ]
            },
        )
        entries = client.get_campaign_entries(campaign_id="c1")
        assert len(entries) == 1
        assert entries[0].id == "ce1"
