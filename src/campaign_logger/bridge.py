"""Serve the read-only MCP server to sandboxed agents over a systemd user socket.

A sandboxed agent cannot start ``campaign-logger mcp`` on the host itself. It
connects to a unix socket instead, and systemd starts one ``campaign-logger mcp``
per connection with stdin and stdout on that socket. Nothing idles between
connections, and nothing is installed or enabled until ``bridge start`` asks.

The socket is ``$XDG_RUNTIME_DIR/campaign-logger-mcp-ro/campaign-logger.sock``:
directory ``0700``, socket ``0600``. **The directory holds this socket and
nothing else**, so a sandbox mounts the directory read-only and can reach the
read-only server and no other socket.

Write access is a separate, opt-in pair of units, selected with ``--write``:
``$XDG_RUNTIME_DIR/campaign-logger-mcp-rw/campaign-logger-write.sock``, in a
directory of its own that no sandbox mounts unless the owner adds it. Nothing
starts it unless ``bridge start --write`` is run by name, and nothing makes the
read socket serve write tools.

``bridge start`` creates that directory itself and checks it before anything
is written. ``DirectoryMode=`` only applies to directories systemd creates, and
a directory that already exists may not be ours: Docker creates a missing
bind-mount source as ``root:root 0755``, which is how the shared
``agent-sandbox`` directory this replaced became unusable.

No credential is written into a unit. The service runs as the user and reads
``~/.campaign_logger.json`` exactly as ``campaign-logger mcp`` does.
"""

import errno
import os
import shutil
import stat
import subprocess  # nosec B404 - fixed argv to systemctl, never a shell
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import click

SOCKET_UNIT = "campaign-logger-bridge.socket"
SERVICE_UNIT = "campaign-logger-bridge@.service"
#: Directly under ``$XDG_RUNTIME_DIR`` and used by this socket alone; see the module docstring.
SOCKET_DIR = "campaign-logger-mcp-ro"
SOCKET_NAME = "campaign-logger.sock"
SOCKET_RELATIVE = f"{SOCKET_DIR}/{SOCKET_NAME}"

WRITE_SOCKET_UNIT = "campaign-logger-bridge-write.socket"
WRITE_SERVICE_UNIT = "campaign-logger-bridge-write@.service"
#: Never the read socket's directory: a sandbox mounts a socket's directory, so sharing one would expose both.
WRITE_SOCKET_DIR = "campaign-logger-mcp-rw"
WRITE_SOCKET_NAME = "campaign-logger-write.sock"


@dataclass(frozen=True)
class Mode:
    """One independent socket and service pair: the read-only default, or the opt-in write pair."""

    write: bool
    socket_unit: str
    service_unit: str
    socket_dir: str
    socket_name: str

    @property
    def socket_relative(self) -> str:
        """The socket's path under ``$XDG_RUNTIME_DIR``."""
        return f"{self.socket_dir}/{self.socket_name}"

    @property
    def start_command(self) -> str:
        """The command that starts this pair, for error messages."""
        return "campaign-logger bridge start" + (" --write" if self.write else "")

    @property
    def label(self) -> str:
        """The mode's name as the commands print it."""
        return "read-write" if self.write else "read-only"


READ = Mode(write=False, socket_unit=SOCKET_UNIT, service_unit=SERVICE_UNIT, socket_dir=SOCKET_DIR, socket_name=SOCKET_NAME)
WRITE = Mode(
    write=True,
    socket_unit=WRITE_SOCKET_UNIT,
    service_unit=WRITE_SERVICE_UNIT,
    socket_dir=WRITE_SOCKET_DIR,
    socket_name=WRITE_SOCKET_NAME,
)


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


def render_socket(mode: Mode = READ) -> str:
    """Render the ``.socket`` unit that listens for sandboxed agents."""
    return (
        "[Unit]\n"
        f"Description=Campaign Logger {mode.label} MCP bridge for sandboxed agents\n"
        "\n"
        "[Socket]\n"
        f"ListenStream=%t/{mode.socket_relative}\n"
        "SocketMode=0600\n"
        "DirectoryMode=0700\n"
        "RemoveOnStop=yes\n"
        "Accept=yes\n"
        "\n"
        "[Install]\n"
        "WantedBy=sockets.target\n"
    )


def render_service(exe: str, mode: Mode = READ) -> str:
    """Render the per-connection ``.service`` template; ``mode`` picks the read-only or the write server.

    Args:
        exe: Absolute path to the ``campaign-logger`` executable.
        mode: The pair being rendered. Only the write pair's service passes ``--write``.
    """
    return (
        "[Unit]\n"
        f"Description=Campaign Logger {mode.label} MCP server for one bridge connection\n"
        "\n"
        "[Service]\n"
        f"ExecStart={_exec_quote(exe)} mcp{' --write' if mode.write else ''}\n"
        "StandardInput=socket\n"
        "StandardOutput=socket\n"
        "StandardError=journal\n"
    )


def unit_dir() -> Path:
    """Return the systemd user unit directory, honouring ``XDG_CONFIG_HOME``."""
    config_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config_home) / "systemd" / "user"


def socket_path(mode: Mode = READ) -> str:
    """Return the socket path as systemd will create it, for display."""
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    return f"{runtime}/{mode.socket_relative}" if runtime else f"$XDG_RUNTIME_DIR/{mode.socket_relative}"


def ensure_socket_dir(mode: Mode = READ) -> Path:
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
    directory = Path(runtime) / mode.socket_dir
    try:
        directory.mkdir(mode=0o700)
    except FileExistsError:
        pass
    except OSError as e:
        raise BridgeError(f"cannot create {directory}: {e.strerror or e}") from e
    not_a_directory = BridgeError(f"{directory} exists and is not a directory; remove it and run `{mode.start_command}` again.")
    if os.name != "posix":
        if directory.is_symlink() or not directory.is_dir():
            raise not_a_directory
        return directory
    # Check and tighten through one descriptor opened without following a
    # symlink, so the directory checked is the directory changed.
    try:
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as e:
        if e.errno in (errno.ENOTDIR, errno.ELOOP):
            raise not_a_directory from e
        raise BridgeError(f"cannot open {directory}: {e.strerror or e}") from e
    try:
        info = os.fstat(fd)
        if info.st_uid != os.getuid():
            raise BridgeError(
                f"{directory} is owned by uid {info.st_uid}, not by you (uid {os.getuid()}), so the socket cannot be created there;"
                " Docker makes a missing bind-mount source as root."
                f" Remove it (as root) and run `{mode.start_command}` again."
            )
        if stat.S_IMODE(info.st_mode) != 0o700:
            os.fchmod(fd, 0o700)
    finally:
        os.close(fd)
    return directory


def check_socket_free(directory: Path, mode: Mode = READ) -> None:
    """Refuse to start over a socket file this bridge is not serving.

    The hand-run ``socat`` bridge this replaces used the same directory and
    socket name. Nothing here deletes a socket or connects to one to test it:
    the owner stops whatever holds it.

    Raises:
        BridgeError: the socket file exists and the bridge's socket unit is not active.
    """
    path = directory / mode.socket_name
    if not os.path.lexists(path):
        return
    if systemctl("is-active", mode.socket_unit, check=False).stdout.strip() == "active":
        return  # ours: ``bridge start`` run again
    # The read pair's directory and name are the ones the hand-run socat bridge used; the write pair has no such predecessor.
    stop_hint = " (the hand-run bridge: `systemctl --user stop campaign-logger-mcp-ro`)" if not mode.write else ""
    raise BridgeError(
        f"{path} already exists and {mode.socket_unit} is not serving it."
        f" Stop whatever made it{stop_hint},"
        f" delete the file if it remains, and run `{mode.start_command}` again."
    )


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


def write_units(directory: Path, exe: str, mode: Mode = READ) -> list[Path]:
    """Write both of ``mode``'s unit files into ``directory`` where they differ.

    Returns:
        The files that were written; unchanged files are left alone.
    """
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in ((mode.socket_unit, render_socket(mode)), (mode.service_unit, render_service(exe, mode))):
        path = directory / name
        if not path.exists() or path.read_text() != text:
            path.write_text(text)
            written.append(path)
    return written


def start(echo: Callable[[str], None], mode: Mode = READ) -> None:
    """Write the units, reload systemd, and enable and start the socket."""
    _require_systemctl()
    if mode.write:
        # Said first, before any check or systemctl call: a supervisor may run this with nobody to ask.
        echo(
            f"WRITE MODE: opening {socket_path(mode)}. An agent connected to it can create, update and delete"
            " campaign data using your credentials. Stop it with: campaign-logger bridge stop --write"
        )
    # Checks first, so a refusal is never read as a half-started bridge.
    check_socket_free(ensure_socket_dir(mode), mode)
    directory = unit_dir()
    exe = executable()
    echo(f"Writing {mode.socket_unit} and {mode.service_unit} to {directory} (if changed).")
    if mode.write:
        echo(f"Each connection will run: {exe} mcp --write (read-write: every write tool is available).")
    else:
        echo(f"Each connection will run: {exe} mcp (read-only; no write tools).")
    echo(f"Enabling and starting {mode.socket_unit}, listening at {socket_path(mode)}.")
    write_units(directory, exe, mode)
    systemctl("daemon-reload")
    systemctl("enable", "--now", mode.socket_unit)
    echo(f"Bridge started. Stop it with: campaign-logger bridge stop{' --write' if mode.write else ''}")


def stop(echo: Callable[[str], None], mode: Mode = READ) -> None:
    """Disable and stop the socket. The unit files are left in place."""
    _require_systemctl()
    echo(f"Disabling and stopping {mode.socket_unit}; {socket_path(mode)} will be removed.")
    systemctl("disable", "--now", mode.socket_unit)
    echo(f"Bridge stopped. The unit files remain in {unit_dir()}; delete them and run `systemctl --user daemon-reload` to remove them.")


def _may_be_active(mode: Mode) -> bool:
    """Whether ``mode``'s pair could exist: its unit file is installed or its socket file is present.

    A pair that was never started has neither, so reporting it needs no ``systemctl`` call. A socket file
    with the unit file deleted is still reported, so an open write socket is never hidden.
    """
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    socket_file = Path(runtime) / mode.socket_relative if runtime else None
    return (unit_dir() / mode.socket_unit).exists() or (socket_file is not None and os.path.lexists(socket_file))


def _report(echo: Callable[[str], None], mode: Mode, *, ask: bool) -> None:
    state = (systemctl("is-active", mode.socket_unit, check=False).stdout.strip() or "unknown") if ask else "not installed"
    echo(f"{mode.label}:")
    echo(f"{mode.socket_unit}: {state}")
    echo(f"socket: {socket_path(mode)}")


def status(echo: Callable[[str], None], mode: Mode | None = None) -> None:
    """Report whether the socket unit is active, and where it listens.

    With no ``mode`` both sockets are reported, each labelled, so an open write socket is never hidden.
    """
    _require_systemctl()
    if mode is not None:
        _report(echo, mode, ask=True)
        return
    _report(echo, READ, ask=True)
    _report(echo, WRITE, ask=_may_be_active(WRITE))


write_option = click.option(
    "--write",
    "write",
    is_flag=True,
    help="Act on the separate READ-WRITE socket, where a connected agent can change campaign data. Never started unless named.",
)


@click.group()
def bridge():
    """Serve the MCP server to sandboxed agents over a unix socket.

    Nothing is enabled until `bridge start`. The default socket serves read tools only;
    `--write` selects a separate, explicitly named read-write socket.
    """


def _run(action: Callable[[Callable[[str], None]], None]) -> None:
    try:
        action(click.echo)
    except (BridgeError, OSError) as e:
        raise click.ClickException(str(e)) from e


@bridge.command(name="start")
@write_option
def start_command(write: bool):
    """Write and enable the systemd user socket that serves the read-only server (or, with --write, the read-write one)."""
    _run(lambda echo: start(echo, WRITE if write else READ))


@bridge.command(name="stop")
@write_option
def stop_command(write: bool):
    """Disable and stop the bridge socket (the read-write one with --write)."""
    _run(lambda echo: stop(echo, WRITE if write else READ))


@bridge.command(name="status")
@write_option
def status_command(write: bool):
    """Show whether the bridge sockets are active and where they listen (only the read-write one with --write)."""
    _run(lambda echo: status(echo, WRITE if write else None))
