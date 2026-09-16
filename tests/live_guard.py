"""G2 -- ``HttpEffectGuard``, a transport-level interlock for live test runs.

The guard wraps a :class:`requests.Session` and inspects every outbound request
*after* the client has built it but *before* it leaves the process. A request the
active phase does not permit raises :class:`LiveGuardViolation` -- never a
warning, never a log line, because the whole point is to fail closed.

Sitting below the client means it also catches what a *helper* does: a
``save()`` inside what was meant to be a read test, or a future API method
nobody remembered to classify. That is what makes "read-only" structural rather
than a naming convention.

See issue #62 section 2 (G2). The sacrificial-campaign and ledger predicates
(G3/G4) are injected as callables so this module stays independent of how those
are discovered; both default to refusing everything.
"""

from urllib.parse import urlsplit

#: (connect, read) timeout forced onto every live request -- Phase 0.1.
#: No request in ``api.py`` sets a timeout and the ``Session`` is built
#: internally, so a caller cannot impose one. Until #43 lands, the live
#: transport imposes it here. pytest-timeout supplies the second layer.
DEFAULT_TIMEOUT = (5, 30)

#: Phases, in escalating order. Each is a superset of the previous one's rights.
READ = "read"
WRITE = "write"
DELETE = "delete"

PHASES = (READ, WRITE, DELETE)

#: POSTs that do not create anything. Verified against api.py: both endpoints
#: take a payload and return a result without persisting it. They are still
#: POSTs against a live service, so they are gated by their own opt-in
#: (``allow_generator_posts`` / ``--run-live-generators``) rather than riding
#: along with the read phase.
EFFECT_FREE_POST_PATHS = frozenset(
    {
        "/api2/generators/validate",
        "/api2/generators/generate",
    }
)

#: Collection segments whose bare form (a trailing slash, no id) means an id was
#: empty at the call site. ``LoggerClient._delete`` builds
#: ``f"{base}/{resource_type}/{item_id}"`` with no check that ``item_id`` is
#: non-empty, so ``DELETE /campaigns/`` is reachable from a single bad variable.
COLLECTION_SEGMENTS = frozenset(
    {
        "campaigns",
        "logs",
        "log-entries",
        "campaign-entries",
        "player-logs",
        "player-log-entries",
        "generators",
    }
)


class LiveGuardViolation(AssertionError):
    """Raised when a request is not permitted by the active live phase.

    Derives from :class:`AssertionError` so a violation surfaces as a test
    failure rather than something a bare ``except Exception`` in client code
    might swallow.
    """


def _deny_all(url, body=None):
    """Default predicate: refuse. G3/G4 supply the real ones."""
    return False


class HttpEffectGuard:
    """Permit only the requests the active phase allows.

    :param phase: one of :data:`READ`, :data:`WRITE`, :data:`DELETE`.
    :param allow_generator_posts: permit the effect-free generator POSTs in
        :data:`EFFECT_FREE_POST_PATHS`. Independent of ``phase``: no phase
        grants it, and it grants no phase.
    :param is_sacrificial_target: ``(url, body) -> bool``, deciding whether a
        request resolves into the sacrificial campaign (G3). Gates POST/PATCH
        in write phase. It receives the body because ``create_log`` and
        ``create_campaign_entry`` name their target campaign **in the payload**,
        not the URL -- a URL-only check cannot tell a sandbox create from one at
        the account root.
    :param is_ledger_id: predicate deciding whether a URL's target id was
        recorded by this run (G4). Gates DELETE in delete phase.
    :param timeout: ``(connect, read)`` forced onto every request the guard
        lets through (Phase 0.1). ``None`` leaves the caller's timeout alone,
        which for this client means no timeout at all -- only pass it in tests.
    """

    def __init__(
        self,
        phase,
        allow_generator_posts=False,
        is_sacrificial_target=None,
        is_ledger_id=None,
        timeout=DEFAULT_TIMEOUT,
    ):
        """Build a guard for one phase. See the class docstring for the arguments."""
        if phase not in PHASES:
            raise ValueError(f"unknown phase {phase!r}; expected one of {PHASES}")
        self.phase = phase
        self.allow_generator_posts = allow_generator_posts
        self.timeout = timeout
        self._is_sacrificial_target = is_sacrificial_target or _deny_all
        self._is_ledger_id = is_ledger_id or _deny_all
        #: Every request the guard allowed, as (method, url). For the §5 capture.
        self.allowed = []

    def check(self, method, url, body=None):
        """Raise :class:`LiveGuardViolation` unless this request is permitted."""
        method = method.upper()
        path = urlsplit(url).path

        # Checked first, and for every method: a bare collection URL means an id
        # was empty upstream, which is a bug whichever phase we are in.
        self._reject_bare_collection(method, url, path)

        if method == "GET":
            self.allowed.append((method, url))
            return

        if method == "POST" and path in EFFECT_FREE_POST_PATHS:
            if not self.allow_generator_posts:
                raise LiveGuardViolation(
                    f"POST {url} is effect-free but still live; it needs --run-live-generators, which no phase implies (phase={self.phase})"
                )
            self.allowed.append((method, url))
            return

        if method in ("POST", "PATCH", "PUT"):
            self._check_write(method, url, body)
        elif method == "DELETE":
            self._check_delete(method, url)
        else:
            raise LiveGuardViolation(f"{method} {url} is not permitted in any phase (phase={self.phase})")

        self.allowed.append((method, url))

    def _reject_bare_collection(self, method, url, path):
        segments = path.split("/")
        if segments and segments[-1] == "":
            parent = segments[-2] if len(segments) >= 2 else ""
            if parent in COLLECTION_SEGMENTS:
                raise LiveGuardViolation(
                    f"{method} {url} targets the bare collection {parent!r} with an empty id. "
                    "Refusing: an empty id here can address the whole collection."
                )

    def _check_write(self, method, url, body=None):
        if self.phase == READ:
            raise LiveGuardViolation(f"{method} {url} attempts a write during the read-only phase")
        if not self._is_sacrificial_target(url, body):
            raise LiveGuardViolation(
                f"{method} {url} does not resolve into the sacrificial campaign. Writes are confined to that container."
            )

    def _check_delete(self, method, url):
        if self.phase != DELETE:
            raise LiveGuardViolation(f"{method} {url} attempts a delete during the {self.phase} phase")
        if not self._is_ledger_id(url):
            raise LiveGuardViolation(f"{method} {url} targets an id this run did not create. Only ledger-recorded objects may be deleted.")

    def install(self, session):
        """Wrap ``session.send`` so every request routes through :meth:`check`.

        Returns the session, so it can be used inline in a fixture.

        Also forces :attr:`timeout` onto any request that does not already
        carry one, so a hung server cannot stall a live run indefinitely.

        The underlying send is resolved from the class *at call time* rather
        than captured here. Capturing the bound method freezes the transport as
        it was at install time, so anything that patches ``Session.send``
        afterwards -- ``requests_mock`` in a test, a recorder in the capture
        pass -- gets bypassed and the request goes to the real network instead.
        """

        def guarded_send(request, **kwargs):
            self.check(request.method, request.url, getattr(request, "body", None))
            if self.timeout is not None and not kwargs.get("timeout"):
                kwargs["timeout"] = self.timeout
            return type(session).send(session, request, **kwargs)

        session.send = guarded_send
        return session
