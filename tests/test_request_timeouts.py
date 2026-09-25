"""Every API request must carry a timeout (#43).

``requests`` applies none by default, so a server that accepts a connection and
then stops responding hangs the caller forever. Before this, 6 of the 25 requests
in ``api.py`` set ``timeout=30`` and the other 19 set nothing -- and the bare ones
were the reads and deletes, so the most-used paths were the exposed ones.

The timeout is applied in :meth:`TimeoutSession.send`, so these tests assert at
the **transport** boundary: what ``HTTPAdapter.send`` was actually handed. A test
that inspected the call sites instead would pass while the value was dropped
somewhere in between.
"""

import ast
from pathlib import Path

import pytest
import requests

# ``requests/__init__.py`` does not re-export the ``adapters`` submodule, so
# ``import requests`` alone leaves ``requests.adapters`` invisible to a type
# checker even though it resolves at runtime.
import requests.adapters  # noqa: F401

from campaign_logger.api import DEFAULT_TIMEOUT
from campaign_logger.api import GeneratorClient
from campaign_logger.api import LoggerClient
from campaign_logger.api import LoggerSession
from campaign_logger.api import TimeoutSession

API_SOURCE = Path(__file__).parent.parent / "src" / "campaign_logger" / "api.py"


class Transport(list):
    """The timeouts seen at the adapter, plus the body it should answer with."""

    body = b'{"data": []}'


@pytest.fixture
def seen_timeouts(monkeypatch):
    """Record the ``timeout`` every request reaches the adapter with.

    Patched at :class:`requests.adapters.HTTPAdapter` rather than at the session,
    so what is asserted is the value that would have gone to the socket.
    """
    seen = Transport()
    real_send = requests.adapters.HTTPAdapter.send

    def spy(self, request, stream=False, timeout=None, **kwargs):
        seen.append(timeout)
        response = requests.Response()
        response.status_code = 200
        response.url = request.url or ""
        response._content = seen.body
        response.request = request
        return response

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", spy)
    assert real_send is not spy  # nosec
    return seen


# --- the default reaches the wire --------------------------------------------


@pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete", "head", "options"])
def test_every_verb_gets_the_default_timeout(seen_timeouts, method):
    """Not just the verbs that happen to be used today."""
    session = TimeoutSession()
    getattr(session, method)("https://example.invalid/thing")
    assert seen_timeouts == [DEFAULT_TIMEOUT]


def test_a_prepared_request_sent_directly_also_gets_one(seen_timeouts):
    """``send`` is the choke point, so bypassing ``get``/``post`` changes nothing."""
    session = TimeoutSession()
    prepared = session.prepare_request(requests.Request("GET", "https://example.invalid/thing"))
    session.send(prepared)
    assert seen_timeouts == [DEFAULT_TIMEOUT]


def test_both_clients_send_a_timeout(seen_timeouts):
    """The two clients build their sessions separately; both must be covered."""
    LoggerClient(base_url="https://example.invalid", client_id="i", client_secret="s").get_campaigns()
    assert seen_timeouts == [DEFAULT_TIMEOUT]

    seen_timeouts.body = b"[]"  # the generator API answers with a bare list
    GeneratorClient(base_url="https://example.invalid", token="t").list_generators()
    assert seen_timeouts == [DEFAULT_TIMEOUT, DEFAULT_TIMEOUT]


def test_logger_session_still_strips_auth_on_redirect():
    """#39's protection must survive changing LoggerSession's base class."""
    assert issubclass(LoggerSession, TimeoutSession)
    assert LoggerSession.AUTH_HEADERS == ("api-client", "api-secret")
    assert LoggerSession.rebuild_auth is not requests.Session.rebuild_auth


# --- an explicit timeout wins -------------------------------------------------


def test_an_explicit_timeout_is_not_overridden(seen_timeouts):
    """This sets a default, not a ceiling."""
    TimeoutSession().get("https://example.invalid/thing", timeout=1.5)
    assert seen_timeouts == [1.5]


def test_explicit_none_means_wait_forever(seen_timeouts):
    """A caller that genuinely wants no timeout must be able to say so.

    ``timeout=None`` is indistinguishable from "unset" in ``kwargs``, so this is
    the one case the implementation cannot honour and the test records it. Set
    ``session.timeout = None`` instead, which the next test covers.
    """
    TimeoutSession().get("https://example.invalid/thing", timeout=None)
    assert seen_timeouts == [DEFAULT_TIMEOUT]


@pytest.mark.parametrize("configured", [None, 2, (1, 2)])
def test_the_client_timeout_argument_is_honoured(seen_timeouts, configured):
    """Including ``None``, which is how a caller opts out entirely."""
    LoggerClient(base_url="https://example.invalid", client_id="i", client_secret="s", timeout=configured).get_campaigns()
    assert seen_timeouts == [configured]


# --- the guard: a new request cannot quietly go without ----------------------


def test_no_call_site_needs_to_remember_a_timeout():
    """``api.py`` must not reintroduce per-call ``timeout=`` arguments.

    Six of them existed and nineteen requests lacked one, which is the failure
    mode of a per-call convention: it looks handled at the sites that have it. The
    session is now the single place, so a ``timeout=`` keyword on a call site here
    means someone is drifting back -- or overriding deliberately, in which case
    this test is the conversation about it.
    """
    tree = ast.parse(API_SOURCE.read_text(encoding="utf-8"))
    offenders = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "session"
        and any(kw.arg == "timeout" for kw in node.keywords)
    ]
    assert not offenders, f"api.py passes timeout= at lines {offenders}; set it on the session instead"


def test_the_sessions_both_default_timeouts():
    """Neither client may be built on a plain ``requests.Session``."""
    logger = LoggerClient(client_id="i", client_secret="s")
    generator = GeneratorClient(token="t")
    for session in (logger.session, generator.session):
        assert isinstance(session, TimeoutSession)
        assert session.timeout == DEFAULT_TIMEOUT


def test_the_default_has_a_connect_and_a_read_half():
    """A single number would apply the generous read budget to connecting too."""
    connect, read = DEFAULT_TIMEOUT
    assert 0 < connect < read
