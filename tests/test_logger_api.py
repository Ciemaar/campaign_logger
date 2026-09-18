import pytest
import requests
import requests_mock
import wire

from campaign_logger.api import BODY_PREVIEW_CHARS
from campaign_logger.api import LoggerClient

BASE_URL = "https://logger-staging.campaign-logger.com"


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
        m.get(f"{BASE_URL}/campaigns/c1", json=wire.document("campaigns", "c1", title="My Campaign"))
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


def test_get_player_logs(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/player-logs", json={"data": [{"id": "pl1", "type": "player-logs", "attributes": {"campaign-id": "c1"}}]})
        result = client.get_player_logs()
        assert len(result) == 1  # nosec
        assert result[0].id == "pl1"  # nosec


def test_get_player_log(client):
    with requests_mock.Mocker() as m:
        m.get(
            f"{BASE_URL}/player-logs/pl1",
            json={"data": {"id": "pl1", "type": "player-logs", "attributes": {"campaign-id": "c1"}}},
        )
        result = client.get_player_log("pl1")
        assert result.id == "pl1"  # nosec


def test_create_player_log(client):
    with requests_mock.Mocker() as m:
        m.post(
            f"{BASE_URL}/player-logs",
            json={"data": {"id": "pl1", "type": "player-logs", "attributes": {"title": "Player Log", "campaign-id": "c1"}}},
        )
        result = client.create_player_log("c1", "Player Log", "Desc")
        assert result.id == "pl1"  # nosec


def test_update_player_log(client):
    with requests_mock.Mocker() as m:
        m.patch(
            f"{BASE_URL}/player-logs/pl1",
            json={"data": {"id": "pl1", "type": "player-logs", "attributes": {"title": "New Title"}}},
        )
        result = client.update_player_log("pl1", title="New Title", description="New Desc")
        assert result.id == "pl1"  # nosec


def test_delete_player_log(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/player-logs/pl1", status_code=204)
        client.delete_player_log("pl1")


def test_get_player_log_entries(client):
    with requests_mock.Mocker() as m:
        m.get(
            f"{BASE_URL}/player-log-entries",
            json={"data": [{"id": "ple1", "type": "player-log-entries", "attributes": {"log-id": "pl1"}}]},
        )
        result = client.get_player_log_entries()
        assert len(result) == 1  # nosec
        assert result[0].id == "ple1"  # nosec


def test_get_player_log_entry(client):
    with requests_mock.Mocker() as m:
        m.get(
            f"{BASE_URL}/player-log-entries/ple1",
            json={"data": {"id": "ple1", "type": "player-log-entries", "attributes": {"log-id": "pl1"}}},
        )
        result = client.get_player_log_entry("ple1")
        assert result.id == "ple1"  # nosec


def test_create_player_log_entry(client):
    with requests_mock.Mocker() as m:
        m.post(
            f"{BASE_URL}/player-log-entries",
            json={"data": {"id": "ple1", "type": "player-log-entries", "attributes": {"log-id": "pl1"}}},
        )
        result = client.create_player_log_entry("pl1", "text")
        assert result.id == "ple1"  # nosec


def test_update_player_log_entry(client):
    with requests_mock.Mocker() as m:
        m.patch(
            f"{BASE_URL}/player-log-entries/ple1",
            json={"data": {"id": "ple1", "type": "player-log-entries", "attributes": {"log-id": "pl1"}}},
        )
        result = client.update_player_log_entry("ple1", "new text")
        assert result.id == "ple1"  # nosec


def test_delete_player_log_entry(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/player-log-entries/ple1", status_code=204)
        client.delete_player_log_entry("ple1")


def test_campaign_methods(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaigns/c1", json=wire.document("campaigns", "c1", title="My Campaign"))
        campaign = client.get_campaign("c1")

        m.get(f"{BASE_URL}/logs", json={"data": [{"id": "l1", "type": "logs", "attributes": {"campaign-id": "c1"}}]})
        logs = campaign.get_logs()
        assert len(logs) == 1  # nosec
        assert logs[0].id == "l1"  # nosec

        m.post(f"{BASE_URL}/logs", json={"data": {"id": "l2", "type": "logs", "attributes": {"campaign-id": "c1"}}})
        new_log = campaign.create_log("Test Log")
        assert new_log.id == "l2"  # nosec

        m.get(
            f"{BASE_URL}/campaign-entries",
            json={"data": [{"id": "ce1", "type": "campaign-entries", "attributes": {"campaign-id": "c1"}}]},
        )
        entries = campaign.get_entries()
        assert len(entries) == 1  # nosec

        m.post(
            f"{BASE_URL}/campaign-entries",
            json={"data": {"id": "ce2", "type": "campaign-entries", "attributes": {"campaign-id": "c1"}}},
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

        m.get(
            f"{BASE_URL}/player-logs",
            json={"data": [{"id": "pl1", "type": "player-logs", "attributes": {"campaign-id": "c1"}}]},
        )
        plogs = campaign.get_player_logs()
        assert len(plogs) == 1  # nosec

        m.post(
            f"{BASE_URL}/player-logs",
            json={"data": {"id": "pl2", "type": "player-logs", "attributes": {"campaign-id": "c1"}}},
        )
        new_plog = campaign.create_player_log("Title")
        assert new_plog.id == "pl2"  # nosec


def test_player_log_methods(client):
    with requests_mock.Mocker() as m:
        m.get(
            f"{BASE_URL}/player-logs/pl1",
            json={"data": {"id": "pl1", "type": "player-logs", "attributes": {"campaign-id": "c1"}}},
        )
        plog = client.get_player_log("pl1")

        m.get(
            f"{BASE_URL}/player-log-entries",
            json={"data": [{"id": "ple1", "type": "player-log-entries", "attributes": {"log-id": "pl1"}}]},
        )
        entries = plog.get_entries()
        assert len(entries) == 1  # nosec

        m.post(
            f"{BASE_URL}/player-log-entries",
            json={"data": {"id": "ple2", "type": "player-log-entries", "attributes": {"log-id": "pl1"}}},
        )
        new_entry = plog.create_entry("text")
        assert new_entry.id == "ple2"  # nosec

        m.patch(f"{BASE_URL}/player-logs/pl1", json={"data": {"id": "pl1", "type": "player-logs"}})
        plog.title = "Updated"
        upd = plog.save()
        assert upd.id == "pl1"  # nosec

        m.delete(f"{BASE_URL}/player-logs/pl1", status_code=204)
        plog.delete()
        assert m.called  # nosec


def test_player_log_entry_methods(client):
    with requests_mock.Mocker() as m:
        m.get(
            f"{BASE_URL}/player-log-entries/ple1",
            json={"data": {"id": "ple1", "type": "player-log-entries", "attributes": {"log-id": "pl1"}}},
        )
        entry = client.get_player_log_entry("ple1")

        m.patch(f"{BASE_URL}/player-log-entries/ple1", json={"data": {"id": "ple1", "type": "player-log-entries"}})
        entry.raw_text = "new text"
        upd = entry.save()
        assert upd.id == "ple1"  # nosec

        m.delete(f"{BASE_URL}/player-log-entries/ple1", status_code=204)
        entry.delete()
        assert m.called  # nosec


def test_log_methods(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/logs/l1", json={"data": {"id": "l1", "type": "logs", "attributes": {"campaign-id": "c1"}}})
        log_obj = client.get_log("l1")

        m.get(f"{BASE_URL}/log-entries", json={"data": [{"id": "le1", "type": "log-entries", "attributes": {"log-id": "l1"}}]})
        entries = log_obj.get_entries()
        assert len(entries) == 1  # nosec

        m.post(f"{BASE_URL}/log-entries", json={"data": {"id": "le2", "type": "log-entries", "attributes": {"log-id": "l1"}}})
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
        m.get(f"{BASE_URL}/log-entries/le1", json={"data": {"id": "le1", "type": "log-entries", "attributes": {"log-id": "l1"}}})
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
            json={"data": {"id": "ce1", "type": "campaign-entries", "attributes": {"campaign-id": "c1"}}},
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


def test_get_player_logs_list_handling(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/player-logs/pl1", json={"data": [{"id": "pl1", "type": "player-logs"}]})
        try:
            client.get_player_log("pl1")
        except ValueError:
            pass

        m.post(f"{BASE_URL}/player-logs", json={"data": [{"id": "pl1", "type": "player-logs"}]})
        try:
            client.create_player_log("c1", "Title")
        except ValueError:
            pass

        m.patch(f"{BASE_URL}/player-logs/pl1", json={"data": [{"id": "pl1", "type": "player-logs"}]})
        try:
            client.update_player_log("pl1")
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


def test_get_player_log_entries_list_handling(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/player-log-entries/ple1", json={"data": [{"id": "ple1", "type": "player-log-entries"}]})
        try:
            client.get_player_log_entry("ple1")
        except ValueError:
            pass

        m.post(f"{BASE_URL}/player-log-entries", json={"data": [{"id": "ple1", "type": "player-log-entries"}]})
        try:
            client.create_player_log_entry("pl1", "text")
        except ValueError:
            pass

        m.patch(f"{BASE_URL}/player-log-entries/ple1", json={"data": [{"id": "ple1", "type": "player-log-entries"}]})
        try:
            client.update_player_log_entry("ple1", "text")
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
        # The server sent no raw-text, so raw_text reports exactly that and the
        # public body surfaces through the derived .text property.
        assert entry.raw_text is None  # nosec
        assert entry.raw_public == "This is public text"  # nosec
        assert entry.text == "This is public text"  # nosec

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
                    {"id": "e1", "type": "log-entries", "attributes": {"log-id": "l1"}},
                    {"id": "e2", "type": "log-entries", "attributes": {"log-id": "l2"}},
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
                    {"id": "ce1", "type": "campaign-entries", "attributes": {"campaign-id": "c1"}},
                    {"id": "ce2", "type": "campaign-entries", "attributes": {"campaign-id": "c2"}},
                ]
            },
        )
        entries = client.get_campaign_entries(campaign_id="c1")
        assert len(entries) == 1
        assert entries[0].id == "ce1"


def test_unparseable_response_truncates_the_body(client):
    """Phase 0.3 (issue #62): a parse failure must not print the whole body.

    The message lands in pytest output and any CI log, so on a live run the old
    ``response.text`` interpolation printed the entire campaign payload. Only a
    bounded preview is included now.
    """
    secret = "The party found the Duke's letter naming the traitor. " * 10
    assert len(secret) > BODY_PREVIEW_CHARS  # nosec  the point of the test

    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaigns", text=secret, headers={"Content-Type": "text/html"})
        with pytest.raises(requests.exceptions.HTTPError) as excinfo:
            client.get_campaigns()

    message = str(excinfo.value)
    assert secret not in message  # nosec
    assert secret[:BODY_PREVIEW_CHARS] in message  # nosec
    assert secret[BODY_PREVIEW_CHARS:] not in message  # nosec
    assert f"truncated from {len(secret)} chars" in message  # nosec
    # Still diagnostic: where, what status, what type.
    assert f"{BASE_URL}/campaigns" in message  # nosec
    assert "text/html" in message  # nosec
    # The full body remains reachable deliberately, via the attached response.
    response = excinfo.value.response
    assert response is not None  # nosec
    assert response.text == secret  # nosec


def test_unparseable_short_response_is_shown_whole(client):
    """A body under the limit needs no truncation note."""
    body = "not json"
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/campaigns", text=body, headers={"Content-Type": "text/plain"})
        with pytest.raises(requests.exceptions.HTTPError) as excinfo:
            client.get_campaigns()

    message = str(excinfo.value)
    assert body in message  # nosec
    assert "truncated" not in message  # nosec


# --- #75: write payloads must use the kebab-case the API actually reads ------


def _sent_attributes(mocker) -> dict:
    """The attributes block of the last request the client sent."""
    return mocker.last_request.json()["data"]["attributes"]


def test_create_log_entry_sends_kebab_case_body(client):
    """Confirmed live: the API 201s and silently drops a camelCase rawText."""
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/log-entries", json=wire.document("log-entries", "le1"))
        client.create_log_entry("l1", "some text")
        attrs = _sent_attributes(m)

    assert attrs["raw-text"] == "some text"  # nosec
    assert attrs["log-id"] == "l1"  # nosec
    assert "rawText" not in attrs  # nosec
    assert "logId" not in attrs  # nosec


def test_update_log_entry_sends_kebab_case_body(client):
    with requests_mock.Mocker() as m:
        m.patch(f"{BASE_URL}/log-entries/le1", json=wire.document("log-entries", "le1"))
        client.update_log_entry("le1", "new text")
        attrs = _sent_attributes(m)

    assert attrs["raw-text"] == "new text"  # nosec
    assert "rawText" not in attrs  # nosec


def test_create_campaign_entry_sends_kebab_case_body(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/campaign-entries", json=wire.document("campaign-entries", "ce1"))
        client.create_campaign_entry("c1", "page text")
        attrs = _sent_attributes(m)

    assert attrs["raw-text"] == "page text"  # nosec
    assert attrs["campaign-id"] == "c1"  # nosec
    assert "rawText" not in attrs  # nosec


def test_update_campaign_entry_sends_kebab_case_body(client):
    with requests_mock.Mocker() as m:
        m.patch(f"{BASE_URL}/campaign-entries/ce1", json=wire.document("campaign-entries", "ce1"))
        client.update_campaign_entry("ce1", "new page text")
        attrs = _sent_attributes(m)

    assert attrs["raw-text"] == "new page text"  # nosec
    assert "rawText" not in attrs  # nosec


def test_create_player_log_entry_sends_kebab_case_body(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/player-log-entries", json=wire.document("player-log-entries", "ple1"))
        client.create_player_log_entry("pl1", "player text")
        attrs = _sent_attributes(m)

    assert attrs["raw-text"] == "player text"  # nosec
    assert attrs["log-id"] == "pl1"  # nosec


def test_update_player_log_entry_sends_kebab_case_body(client):
    with requests_mock.Mocker() as m:
        m.patch(f"{BASE_URL}/player-log-entries/ple1", json=wire.document("player-log-entries", "ple1"))
        client.update_player_log_entry("ple1", "new player text")
        attrs = _sent_attributes(m)

    assert attrs["raw-text"] == "new player text"  # nosec


def test_create_log_and_player_log_send_kebab_case_campaign_id(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/logs", json=wire.document("logs", "l1"))
        client.create_log("c1", "My Log", "desc")
        assert _sent_attributes(m)["campaign-id"] == "c1"  # nosec

        m.post(f"{BASE_URL}/player-logs", json=wire.document("player-logs", "pl1"))
        client.create_player_log("c1", "My Player Log", "desc")
        assert _sent_attributes(m)["campaign-id"] == "c1"  # nosec


def test_no_write_payload_uses_camelcase_attributes():
    """A tripwire for write methods nobody remembered to assert on.

    This is deliberately shallow. It only sees an indented, double-quoted,
    colon-terminated key -- the shape the payload dicts are written in today. It
    does NOT catch a one-line dict, single quotes, ``update(rawText=...)`` or a
    computed key, all of which would reintroduce the bug and pass here.

    The per-method assertions above, which check the body the client actually
    sends, are the load-bearing protection. Do not delete them on the grounds
    that this test covers the surface -- it does not.
    """
    import pathlib
    import re

    source = pathlib.Path("src/campaign_logger/api.py").read_text()
    offenders = re.findall(r'^\s+"([a-z]+[A-Z]\w*)"\s*:', source, re.MULTILINE)
    assert not offenders, f"write payloads must use kebab-case, found: {sorted(set(offenders))}"  # nosec


def test_create_player_log_entry_uses_the_player_log_relationship_name(client):
    """Verified live: "playerLog" and "log" are accepted with 201 and orphan the entry.

    Only "player-log" actually attaches it, so this member name is load-bearing
    in exactly the way the camelCase attribute keys were (#75).
    """
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/player-log-entries", json=wire.document("player-log-entries", "ple1"))
        client.create_player_log_entry("pl1", "text")
        rels = m.last_request.json()["data"]["relationships"]

    assert "player-log" in rels  # nosec
    assert rels["player-log"]["data"] == {"type": "player-logs", "id": "pl1"}  # nosec
    assert "playerLog" not in rels  # nosec


def test_every_write_goes_through_write_payload(client):
    """The envelope is built in one place, so its shape cannot drift per method."""
    import inspect

    source = inspect.getsource(LoggerClient)
    # The only literal {"data": ...} envelope left is the relationship helper.
    assert source.count('"data": {') == 1  # nosec
