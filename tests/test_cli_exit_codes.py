"""A failing command must exit non-zero (#96).

Every command used to wrap its body in ``except Exception as e:
click.echo(f"Error: {e}", err=True)`` and then fall off the end, so Click saw a
normal return and reported success. 48 handlers did this; only two places in the
file exited non-zero, and both were credential checks in group callbacks. So
configuration errors were reported correctly and *every actual operation* was
not, meaning no script, Makefile or CI step could detect a failure.

The interesting test here is :func:`test_every_command_exits_non_zero_on_api_failure`,
which walks the whole command tree rather than a list someone has to remember to
extend. That is the difference between fixing 48 sites and keeping them fixed.
"""

import ast
from pathlib import Path

import click
import pytest
import requests
from click.testing import CliRunner

from campaign_logger.cli import EXPECTED_ERRORS
from campaign_logger.cli import main

CLI_SOURCE = Path(__file__).parent.parent / "src" / "campaign_logger" / "cli.py"

#: Placeholder for any required argument. Its value never matters: the client is
#: rigged to fail before it could.
PLACEHOLDER = "x"

#: Commands that cannot reach the client, so an API failure is not their subject.
#: ``mcp`` is covered by ``tests/test_mcp.py::test_mcp_cli_command_error``.
NOT_CLIENT_BACKED = {("mcp",)}


class FailingClient:
    """A client whose every method raises, whatever it is called.

    Deliberately **not** a ``MagicMock``. A MagicMock creates attributes lazily, so
    rigging it by iterating ``dir()`` sets nothing -- the methods do not exist until
    they are first accessed. An earlier version of this test did exactly that and
    passed vacuously for 38 of 39 commands: the client never failed, so of course
    nothing reported a failure. ``__getattr__`` cannot miss.
    """

    def __getattr__(self, name):
        """Return a callable that fails, for any attribute asked for."""

        def fail(*args, **kwargs):
            raise requests.exceptions.RequestException("the API is unreachable")

        return fail


def leaf_commands(command, path=()):
    """Every runnable command in the tree, with the argv needed to invoke it."""
    if isinstance(command, click.Group):
        for name, sub in command.commands.items():
            yield from leaf_commands(sub, path + (name,))
        return
    argv = [PLACEHOLDER for param in command.params if isinstance(param, click.Argument) and param.required]
    yield path, argv


ALL_LEAVES = [(path, argv) for path, argv in leaf_commands(main) if path not in NOT_CLIENT_BACKED]


def test_the_tree_walk_found_the_commands():
    """Guard against the parametrisation below silently covering nothing."""
    assert len(ALL_LEAVES) >= 30, f"only found {len(ALL_LEAVES)} commands; the walk is probably broken"


@pytest.mark.parametrize("path,argv", ALL_LEAVES, ids=lambda v: " ".join(v) if isinstance(v, tuple) else None)
def test_every_command_exits_non_zero_on_api_failure(path, argv, monkeypatch, mocker, tmp_path):
    """No command may report success when the API call behind it failed.

    Parametrised over the command tree, so a command added later is covered
    without anyone remembering to add it here.
    """
    monkeypatch.setenv("CL_LOGGER_CLIENT_ID", "id")
    monkeypatch.setenv("CL_LOGGER_CLIENT_SECRET", "secret")
    monkeypatch.setenv("CL_GENERATOR_TOKEN", "token")
    monkeypatch.chdir(tmp_path)

    # Some commands take a file argument before they reach the client.
    Path(PLACEHOLDER).write_text('{"name": "g"}', encoding="utf-8")

    for client in ("LoggerClient", "GeneratorClient"):
        mocker.patch(f"campaign_logger.cli.{client}", return_value=FailingClient())

    result = CliRunner().invoke(main, list(path) + argv)

    assert result.exit_code != 0, f"`{' '.join(path)}` reported success while the API was failing.\noutput: {result.output!r}"


# --- structural guards --------------------------------------------------------


def _reports_an_error(handler):
    """Whether ``handler`` is dealing with a failure rather than choosing a path.

    Two signals, because either alone misses cases:

    * it **binds** the exception (``as e``) -- you only need the object to report
      or re-raise it, so binding marks a handler as handling a failure; and
    * it echoes a string containing ``Error``.

    An ``except ImportError:`` that falls back to plain output does neither: it is
    not handling a failure, it is picking a different renderer, and it is right to
    fall through. ``load_config``'s bare ``except OSError: pass`` is the same --
    a missing config file is not an error.
    """
    if handler.name is not None:
        return True
    return any(isinstance(node, ast.Constant) and isinstance(node.value, str) and "Error" in node.value for node in ast.walk(handler))


def _swallowing_handlers(path):
    """Handlers that report a failure and then let the command return normally.

    That is the bug itself: Click treats a normal return as success, so the command
    prints an error and exits 0.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if not _reports_an_error(node):
            continue
        exits = any(
            isinstance(stmt, ast.Raise)
            or (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Attribute)
                and stmt.value.func.attr == "exit"
            )
            for stmt in ast.walk(node)
        )
        if not exits:
            offenders.append(node.lineno)
    return offenders


def test_no_handler_reports_an_error_and_returns_normally():
    """The rule, so the 48 sites cannot come back one at a time."""
    offenders = _swallowing_handlers(CLI_SOURCE)
    assert not offenders, f"cli.py has handlers that report and fall through at lines {offenders}"


def test_expected_errors_does_not_include_exception():
    """``EXPECTED_ERRORS`` must stay a narrow list, or the fix is undone.

    The point is not only the exit code: catching bare ``Exception`` flattened a
    defect in this package into the same one-line message a 404 produces, so a bug
    here was indistinguishable from the server saying no.
    """
    assert Exception not in EXPECTED_ERRORS
    assert BaseException not in EXPECTED_ERRORS
    assert all(issubclass(exc, Exception) for exc in EXPECTED_ERRORS)


def test_a_bug_is_not_flattened_into_an_error_message(monkeypatch, mocker):
    """An unexpected exception must surface as itself, not as ``Error: ...``."""
    monkeypatch.setenv("CL_GENERATOR_TOKEN", "token")
    instance = mocker.MagicMock()
    instance.list_generators.side_effect = AttributeError("'NoneType' object has no attribute 'id'")
    mocker.patch("campaign_logger.cli.GeneratorClient", return_value=instance)

    result = CliRunner().invoke(main, ["generator", "list"])

    assert result.exit_code != 0
    assert isinstance(result.exception, AttributeError)
