import os

import pytest
import requests_mock

from campaign_logger.api import GeneratorClient
from campaign_logger.api import LoggerClient


@pytest.fixture
def mock_requests(request):
    is_live = request.config.getoption("--run-e2e") or os.environ.get("RUN_LIVE_E2E") == "1"

    if is_live:
        yield None
        return

    with requests_mock.Mocker() as m:
        # Mock Generator endpoints
        m.get("https://mock/api2/generators", json=[{"id": "e2e_gen_1", "name": "Mock Gen"}])
        m.get("https://mock/api2/generators/e2e_gen_1", json={"id": "e2e_gen_1", "name": "Mock Gen"})

        # Mock Logger endpoints
        m.get(
            "https://mock/campaigns",
            json={
                "data": [{"type": "campaigns", "id": "mock_camp_1", "attributes": {"title": "Existing Mock Campaign", "description": ""}}]
            },
        )
        m.post(
            "https://mock/campaigns",
            json={
                "data": {
                    "type": "campaigns",
                    "id": "mock_camp_new",
                    "attributes": {"title": "E2E Automated Test Campaign", "description": "Created during CI E2E run."},
                }
            },
        )
        m.post(
            "https://mock/logs",
            json={
                "data": {
                    "type": "logs",
                    "id": "mock_log_new",
                    "attributes": {"title": "E2E Session 1", "description": "Testing log creation", "campaignId": "mock_camp_new"},
                }
            },
        )
        m.post(
            "https://mock/log-entries",
            json={
                "data": {
                    "type": "log-entries",
                    "id": "mock_le_new",
                    "attributes": {"rawText": "The party entered the E2E dungeon.", "logId": "mock_log_new"},
                }
            },
        )
        m.post(
            "https://mock/campaign-entries",
            json={
                "data": {
                    "type": "campaign-entries",
                    "id": "mock_ce_new",
                    "attributes": {"rawText": "E2E Rules Page", "campaignId": "mock_camp_new"},
                }
            },
        )
        m.patch(
            "https://mock/campaign-entries/mock_ce_new",
            json={
                "data": {
                    "type": "campaign-entries",
                    "id": "mock_ce_new",
                    "attributes": {"rawText": "Updated E2E Rules Page", "campaignId": "mock_camp_new"},
                }
            },
        )
        m.delete("https://mock/campaign-entries/mock_ce_new", status_code=204)
        m.delete("https://mock/log-entries/mock_le_new", status_code=204)
        m.delete("https://mock/campaigns/mock_camp_new", status_code=204)
        yield m


@pytest.fixture
def live_generator_client(request, mock_requests):
    """Returns a GeneratorClient. Mocks if not running live."""
    is_live = request.config.getoption("--run-e2e") or os.environ.get("RUN_LIVE_E2E") == "1"

    if is_live:
        token = os.environ.get("CL_GENERATOR_TOKEN")
        if not token:
            pytest.skip("CL_GENERATOR_TOKEN environment variable is not set. Skipping live E2E test.")
        url = os.environ.get("CL_GENERATOR_URL", "https://generator.campaign-logger.com")
        return GeneratorClient(base_url=url, token=token)
    else:
        # Request context ensures we are not modifying items directly but letting the test run with mocked data
        return GeneratorClient(base_url="https://mock", token="mock-token")


@pytest.fixture
def live_logger_client(request, mock_requests):
    """Returns a LoggerClient. Mocks if not running live."""
    is_live = request.config.getoption("--run-e2e") or os.environ.get("RUN_LIVE_E2E") == "1"

    if is_live:
        client_id = os.environ.get("CL_LOGGER_CLIENT_ID")
        client_secret = os.environ.get("CL_LOGGER_CLIENT_SECRET")
        if not client_id or not client_secret:
            pytest.skip("CL_LOGGER_CLIENT_ID or CL_LOGGER_CLIENT_SECRET environment variable is not set. Skipping live E2E test.")
        url = os.environ.get("CL_LOGGER_URL", "https://logger.campaign-logger.com")
        return LoggerClient(base_url=url, client_id=client_id, client_secret=client_secret)
    else:
        return LoggerClient(base_url="https://mock", client_id="mock", client_secret="mock")


@pytest.mark.e2e
def test_generator_client_e2e(live_generator_client):
    """End-to-End test for GeneratorClient."""
    # List all generators to ensure the client connects and authenticates
    generators = live_generator_client.list_generators()
    assert isinstance(generators, list)

    # If the user has at least one generator, fetch it by ID and verify
    if generators:
        first_gen_id = generators[0].id
        assert first_gen_id is not None
        fetched_gen = live_generator_client.get_generator(first_gen_id)
        assert fetched_gen.id == first_gen_id


@pytest.mark.e2e
def test_logger_client_e2e(live_logger_client):
    """End-to-End test for LoggerClient."""
    # 1. Fetch campaigns to ensure connection
    campaigns = live_logger_client.get_campaigns()
    assert isinstance(campaigns, list)

    # 2. Create a temporary campaign for testing
    test_title = "E2E Automated Test Campaign"
    test_desc = "Created during CI E2E run."
    new_campaign = live_logger_client.create_campaign(title=test_title, description=test_desc)

    assert new_campaign.id is not None
    assert new_campaign.title == test_title

    try:
        # 3. Create a Log under the campaign
        test_log_title = "E2E Session 1"
        new_log = new_campaign.create_log(title=test_log_title, description="Testing log creation")
        assert new_log.id is not None
        assert new_log.title == test_log_title
        assert new_log.campaign_id == new_campaign.id

        # 4. Create a Log Entry
        test_entry_text = "The party entered the E2E dungeon."
        new_entry = new_log.create_entry(raw_text=test_entry_text)
        assert new_entry.id is not None
        assert new_entry.raw_text == test_entry_text
        assert new_entry.log_id == new_log.id

        # 5. Create a Campaign Entry (Page)
        test_page_text = "E2E Rules Page"
        new_page = new_campaign.create_entry(raw_text=test_page_text)
        assert new_page.id is not None
        assert new_page.raw_text == test_page_text
        assert new_page.campaign_id == new_campaign.id

        # 6. Update the Page
        updated_text = "Updated E2E Rules Page"
        new_page.raw_text = updated_text
        updated_page = new_page.save()
        assert updated_page.raw_text == updated_text

        # 7. Delete the Page and the Entry
        new_page.delete()
        new_entry.delete()

    finally:
        # 8. Clean up the Campaign regardless of intermediate failures
        new_campaign.delete()
