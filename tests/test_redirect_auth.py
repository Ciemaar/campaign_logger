"""Regression tests for #39 - credentials must not follow a cross-host redirect.

The logger API authenticates with the custom headers ``api-client`` and ``api-secret``,
as specified in PR #1. ``requests`` protects only the standard ``Authorization`` header:
``Session.rebuild_auth`` deletes it when a redirect crosses to a different host and leaves
every other header in place. The logger credentials are therefore forwarded to whatever
host answers a redirect, while the generator client's bearer token is not.

The vulnerable header assignment was introduced in 90c7081 (the #11 squash) and is
unchanged through 0809ece, so the logger test below fails at every commit in that range.
``test_generator_...`` is the control: it exercises the same redirect path and passes,
which is what shows the failure is the header choice and not the test harness.
"""

import secrets

import pytest
import requests_mock

from campaign_logger.api import GeneratorClient
from campaign_logger.api import LoggerClient

API_HOST = "https://logger.campaign-logger.com"
GENERATOR_HOST = "https://generator.campaign-logger.com"
OTHER_HOST = "https://elsewhere.example.com"

# Generated per run rather than hardcoded, per the convention in tests/test_api.py.
CLIENT_ID = secrets.token_hex(16)
CLIENT_SECRET = secrets.token_hex(16)
BEARER_TOKEN = secrets.token_hex(16)


def _redirected_headers(mocker, source, destination):
    """Return the headers of the final request after `source` redirects to `destination`."""
    mocker.get(source, status_code=302, headers={"Location": destination})
    return mocker


@pytest.mark.xfail(
    strict=True,
    reason="#39: api-client/api-secret are custom headers, so requests does not strip them "
    "on a cross-host redirect. Remove this marker when the fix lands.",
)
def test_logger_credentials_are_not_sent_to_a_different_host_after_redirect():
    """The logger client must not forward its credentials across a cross-host redirect."""
    client = LoggerClient(base_url=API_HOST, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    with requests_mock.Mocker() as m:
        _redirected_headers(m, f"{API_HOST}/campaigns", f"{OTHER_HOST}/campaigns")
        m.get(f"{OTHER_HOST}/campaigns", json={"data": []})
        client.get_campaigns()

        final = m.request_history[-1]
        assert final.url.startswith(OTHER_HOST)  # nosec - redirect was followed
        assert "api-client" not in final.headers  # nosec
        assert "api-secret" not in final.headers  # nosec


def test_generator_token_is_not_sent_to_a_different_host_after_redirect():
    """Control: requests already strips Authorization, so the generator client is safe."""
    client = GeneratorClient(base_url=GENERATOR_HOST, token=BEARER_TOKEN)

    with requests_mock.Mocker() as m:
        _redirected_headers(m, f"{GENERATOR_HOST}/api2/generators", f"{OTHER_HOST}/api2/generators")
        m.get(f"{OTHER_HOST}/api2/generators", json={"generators": []})
        client.list_generators()

        final = m.request_history[-1]
        assert final.url.startswith(OTHER_HOST)  # nosec - redirect was followed
        assert "Authorization" not in final.headers  # nosec


def test_logger_credentials_are_still_sent_to_the_api_itself():
    """Guard against 'fixing' #39 by dropping the credentials altogether."""
    client = LoggerClient(base_url=API_HOST, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    with requests_mock.Mocker() as m:
        m.get(f"{API_HOST}/campaigns", json={"data": []})
        client.get_campaigns()

        sent = m.request_history[-1]
        assert sent.headers["api-client"] == CLIENT_ID  # nosec
        assert sent.headers["api-secret"] == CLIENT_SECRET  # nosec
