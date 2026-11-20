"""Serve the read-only MCP server to sandboxed agents over a systemd user socket.

A sandboxed agent cannot start ``campaign-logger mcp`` on the host itself. It
connects to a unix socket instead, and systemd starts one ``campaign-logger mcp``
per connection with stdin and stdout on that socket. Nothing idles between
connections, and nothing is installed or enabled until ``bridge start`` asks.

The socket is ``$XDG_RUNTIME_DIR/campaign-logger-mcp-ro/campaign-logger.sock``:
directory ``0700``, socket ``0600``. **The directory holds this socket and
nothing else**, so a sandbox mounts the directory read-only and can reach the
read-only server and no other socket; a write socket, if one is ever added,
gets a directory of its own that the sandbox does not mount.

``bridge start`` creates that directory itself and checks it before anything
is written. ``DirectoryMode=`` only applies to directories systemd creates, and
a directory that already exists may not be ours: Docker creates a missing
bind-mount source as ``root:root 0755``, which is how the shared
``agent-sandbox`` directory this replaced became unusable.

No credential is written into a unit. The service runs as the user and reads
``~/.campaign_logger.json`` exactly as ``campaign-logger mcp`` does.
"""

import os
import shutil
import stat
import subprocess  # nosec B404 - fixed argv to systemctl, never a shell
import sys
from collections.abc import Callable
from pathlib import Path

import click

SOCKET_UNIT = "campaign-logger-bridge.socket"
SERVICE_UNIT = "campaign-logger-bridge@.service"
#: Directly under ``$XDG_RUNTIME_DIR`` and used by this socket alone; see the module docstring.
SOCKET_DIR = "campaign-logger-mcp-ro"
SOCKET_NAME = "campaign-logger.sock"
SOCKET_RELATIVE = f"{SOCKET_DIR}/{SOCKET_NAME}"


class BridgeError(Exception):
    """The bridge could not be started, stopped or inspected."""


def executable() -> str:
    """Return the absolute path of this installation's ``campaign-logger``.

    ``shutil.which`` finds the script on ``PATH``, which is the installation the
    user is running under a venv or ``uv run``. Failing that, the script that is
    running now is the installation by definition.
    """
    found = shutil.which("campaign-logger")
    if found:
        return str(Path(found).resolve())
    return str(Path(sys.argv[0]).resolve())


def _exec_quote(argument: str) -> str:
    """Quote one ``ExecStart=`` argument for systemd.

    ``%`` starts a specifier in a unit file, so it is doubled. Whitespace,
    quotes and backslashes need the argument double-quoted, with the last two
    escaped.
    """
    argument = argument.replace("%", "%%")
    if any(c in argument for c in " \t\"'\\"):
        return '"' + argument.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return argument


def render_socket() -> str:
    """Render the ``.socket`` unit that listens for sandboxed agents."""
    return (
        "[Unit]\n"
        "Description=Campaign Logger read-only MCP bridge for sandboxed agents\n"
        "\n"
        "[Socket]\n"
        f"ListenStream=%t/{SOCKET_RELATIVE}\n"
        "SocketMode=0600\n"
        "DirectoryMode=0700\n"
        "RemoveOnStop=yes\n"
        "Accept=yes\n"
        "\n"
        "[Install]\n"
        "WantedBy=sockets.target\n"
    )


def render_service(exe: str) -> str:
    """Render the per-connection ``.service`` template running the read-only server.

    Args:
        exe: Absolute path to the ``campaign-logger`` executable.
    """
    return (
        "[Unit]\n"
        "Description=Campaign Logger read-only MCP server for one bridge connection\n"
        "\n"
        "[Service]\n"
        f"ExecStart={_exec_quote(exe)} mcp\n"
        "StandardInput=socket\n"
        "StandardOutput=socket\n"
        "StandardError=journal\n"
    )


def unit_dir() -> Path:
    """Return the systemd user unit directory, honouring ``XDG_CONFIG_HOME``."""
    config_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config_home) / "systemd" / "user"


def socket_path() -> str:
    """Return the socket path as systemd will create it, for display."""
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    return f"{runtime}/{SOCKET_RELATIVE}" if runtime else f"$XDG_RUNTIME_DIR/{SOCKET_RELATIVE}"


def ensure_socket_dir() -> Path:
    """Create the socket's directory, or check the one that exists, and return it.

    The directory must be a real directory owned by this user. If it is ours
    but too open, it is tightened to ``0700``; if it is someone else's, nothing
    is changed and the error says what to do.

    Raises:
        BridgeError: ``XDG_RUNTIME_DIR`` is unset, or the directory cannot be
            created, is not a directory, or belongs to another user.
    """
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime:
        raise BridgeError("XDG_RUNTIME_DIR is not set: the bridge needs a systemd user session.")
    directory = Path(runtime) / SOCKET_DIR
    try:
        directory.mkdir(mode=0o700)
    except FileExistsError:
        pass
    except OSError as e:
        raise BridgeError(f"cannot create {directory}: {e.strerror or e}") from e
    if directory.is_symlink() or not directory.is_dir():
        raise BridgeError(f"{directory} exists and is not a directory; remove it and run `campaign-logger bridge start` again.")
    if os.name == "posix":
        info = directory.stat()
        if info.st_uid != os.getuid():
            raise BridgeError(
                f"{directory} is owned by uid {info.st_uid}, not by you (uid {os.getuid()}), so the socket cannot be created there;"
                " Docker makes a missing bind-mount source as root."
                " Remove it (as root) and run `campaign-logger bridge start` again."
            )
        if stat.S_IMODE(info.st_mode) != 0o700:
            directory.chmod(0o700)
    return directory


def _require_systemctl() -> str:
    found = shutil.which("systemctl")
    if not found:
        raise BridgeError("systemctl not found: the bridge needs a systemd user manager, and there is no fallback.")
    return found


def systemctl(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run ``systemctl --user`` with ``args``.

    Raises:
        BridgeError: systemctl is missing, or ``check`` is set and it failed.
    """
    command = [_require_systemctl(), "--user", *args]
    result = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec B603 - fixed argv, no shell
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        reason = detail[0] if detail else f"exit status {result.returncode}"
        raise BridgeError(f"systemctl --user {' '.join(args)} failed: {reason}")
    return result


def write_units(directory: Path, exe: str) -> list[Path]:
    """Write both unit files into ``directory`` where they differ.

    Returns:
        The files that were written; unchanged files are left alone.
    """
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in ((SOCKET_UNIT, render_socket()), (SERVICE_UNIT, render_service(exe))):
        path = directory / name
        if not path.exists() or path.read_text() != text:
            path.write_text(text)
            written.append(path)
    return written


def start(echo: Callable[[str], None]) -> None:
    """Write the units, reload systemd, and enable and start the socket."""
    _require_systemctl()
    directory = unit_dir()
    exe = executable()
    echo(f"Writing {SOCKET_UNIT} and {SERVICE_UNIT} to {directory} (if changed).")
    echo(f"Each connection will run: {exe} mcp (read-only; no write tools).")
    echo(f"Enabling and starting {SOCKET_UNIT}, listening at {socket_path()}.")
    ensure_socket_dir()
    write_units(directory, exe)
    systemctl("daemon-reload")
    systemctl("enable", "--now", SOCKET_UNIT)
    echo("Bridge started. Stop it with: campaign-logger bridge stop")


def stop(echo: Callable[[str], None]) -> None:
    """Disable and stop the socket. The unit files are left in place."""
    _require_systemctl()
    echo(f"Disabling and stopping {SOCKET_UNIT}; {socket_path()} will be removed.")
    systemctl("disable", "--now", SOCKET_UNIT)
    echo(f"Bridge stopped. The unit files remain in {unit_dir()}; delete them and run `systemctl --user daemon-reload` to remove them.")


def status(echo: Callable[[str], None]) -> None:
    """Report whether the socket unit is active, and where it listens."""
    _require_systemctl()
    state = systemctl("is-active", SOCKET_UNIT, check=False).stdout.strip() or "unknown"
    echo(f"{SOCKET_UNIT}: {state}")
    echo(f"socket: {socket_path()}")


@click.group()
def bridge():
    """Serve the read-only MCP server to sandboxed agents over a unix socket.

    Nothing is enabled until `bridge start`. The socket serves read tools only.
    """


def _run(action: Callable[[Callable[[str], None]], None]) -> None:
    try:
        action(click.echo)
    except (BridgeError, OSError) as e:
        raise click.ClickException(str(e)) from e


@bridge.command(name="start")
def start_command():
    """Write and enable the systemd user socket that serves the read-only server."""
    _run(start)


@bridge.command(name="stop")
def stop_command():
    """Disable and stop the bridge socket."""
    _run(stop)


@bridge.command(name="status")
def status_command():
    """Show whether the bridge socket is active and where it listens."""
    _run(status)
