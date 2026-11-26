"""Tests for ``campaign-logger bridge``, the systemd user socket for sandboxed agents.

No test here touches the real user manager: every ``systemctl`` call goes through
a mocked ``subprocess.run``. The one end-to-end test stands in for systemd with
its own accept loop, which proves the server behaves over a socket -- not that the
units load under a real systemd. That needs a human to run ``bridge start`` once.
"""

import json
import os
import shlex
import shutil
import socket
import stat
import subprocess  # nosec B404 - the stand-in runs the rendered ExecStart with a fixed argv
import sys
import tempfile
import threading
from pathlib import Path

import pytest
from click.testing import CliRunner

from campaign_logger import bridge
from campaign_logger.cli import main

SYSTEMCTL = "/usr/bin/systemctl"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def config_home(tmp_path, monkeypatch):
    home = tmp_path / "xdg-config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home))
    runtime = tmp_path / "run"
    runtime.mkdir(mode=0o700)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
    return home


@pytest.fixture
def runtime_dir(config_home):
    return Path(os.environ["XDG_RUNTIME_DIR"])


POSIX_ONLY = pytest.mark.skipif(os.name != "posix", reason="ownership and modes are POSIX")


@pytest.fixture
def fake_systemctl(mocker):
    """Pretend systemctl exists, and record every call made to it."""
    real_which = shutil.which
    mocker.patch(
        "campaign_logger.bridge.shutil.which",
        side_effect=lambda name: {"systemctl": SYSTEMCTL, "campaign-logger": "/opt/cl/bin/campaign-logger"}.get(name) or real_which(name),
    )
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="active\n", stderr="")

    mocker.patch("campaign_logger.bridge.subprocess.run", side_effect=run)
    return calls


# --- rendering --------------------------------------------------------------


def test_socket_unit_listens_where_the_sandbox_expects_with_private_modes():
    text = bridge.render_socket()
    assert "ListenStream=%t/campaign-logger-mcp-ro/campaign-logger.sock\n" in text
    assert "SocketMode=0600\n" in text
    assert "DirectoryMode=0700\n" in text
    assert "RemoveOnStop=yes\n" in text
    assert "Accept=yes\n" in text
    assert "WantedBy=sockets.target\n" in text


def test_service_runs_this_installation_read_only():
    text = bridge.render_service("/opt/cl/bin/campaign-logger")
    exec_lines = [line for line in text.splitlines() if line.startswith("ExecStart=")]
    assert exec_lines == ["ExecStart=/opt/cl/bin/campaign-logger mcp"]
    assert "--write" not in text
    assert "StandardInput=socket\n" in text
    assert "StandardOutput=socket\n" in text


def test_service_carries_no_credential():
    text = bridge.render_socket() + bridge.render_service("/opt/cl/bin/campaign-logger")
    for forbidden in ("Environment", "CL_", "token", "secret", "client"):
        assert forbidden not in text


def test_service_quotes_a_path_systemd_would_split_or_expand():
    line = next(x for x in bridge.render_service('/home/a b/50%/"q"\\bin/campaign-logger').splitlines() if x.startswith("ExecStart="))
    assert line == 'ExecStart="/home/a b/50%%/\\"q\\"\\\\bin/campaign-logger" mcp'


def test_executable_is_the_one_on_path(mocker, tmp_path):
    script = tmp_path / "campaign-logger"
    script.write_text("")
    mocker.patch("campaign_logger.bridge.shutil.which", return_value=str(script))
    assert bridge.executable() == str(script.resolve())


def test_executable_falls_back_to_the_running_script(mocker, tmp_path):
    mocker.patch("campaign_logger.bridge.shutil.which", return_value=None)
    mocker.patch.object(sys, "argv", [str(tmp_path / "bin" / "campaign-logger")])
    assert bridge.executable() == str((tmp_path / "bin" / "campaign-logger").resolve())


def test_unit_dir_defaults_under_home(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert bridge.unit_dir() == Path.home() / ".config" / "systemd" / "user"


def test_socket_path_without_runtime_dir_names_the_variable(monkeypatch):
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    assert bridge.socket_path() == "$XDG_RUNTIME_DIR/campaign-logger-mcp-ro/campaign-logger.sock"


def test_the_socket_directory_is_its_own():
    """A sandbox mounts the socket's directory, so nothing else may live in it (#168 review)."""
    assert bridge.SOCKET_RELATIVE == f"{bridge.SOCKET_DIR}/{bridge.SOCKET_NAME}"
    assert "/" not in bridge.SOCKET_DIR
    assert bridge.SOCKET_DIR.endswith("-ro")


def test_write_units_leaves_unchanged_files_alone(tmp_path):
    first = bridge.write_units(tmp_path, "/opt/cl/bin/campaign-logger")
    assert {p.name for p in first} == {bridge.SOCKET_UNIT, bridge.SERVICE_UNIT}
    assert bridge.write_units(tmp_path, "/opt/cl/bin/campaign-logger") == []
    assert bridge.write_units(tmp_path, "/other/campaign-logger") == [tmp_path / bridge.SERVICE_UNIT]


# --- the commands -----------------------------------------------------------


def test_start_writes_units_then_reloads_then_enables(runner, config_home, fake_systemctl):
    result = runner.invoke(main, ["bridge", "start"])

    assert result.exit_code == 0, result.output
    unit_dir = config_home / "systemd" / "user"
    written_socket = (unit_dir / bridge.SOCKET_UNIT).read_text()
    assert "ListenStream=%t/campaign-logger-mcp-ro/campaign-logger.sock\n" in written_socket
    assert written_socket == bridge.render_socket()
    assert " mcp\n" in (unit_dir / bridge.SERVICE_UNIT).read_text()
    assert (unit_dir / bridge.SERVICE_UNIT).read_text() == bridge.render_service(bridge.executable())
    assert fake_systemctl == [
        [SYSTEMCTL, "--user", "daemon-reload"],
        [SYSTEMCTL, "--user", "enable", "--now", bridge.SOCKET_UNIT],
    ]


def test_start_says_what_it_will_do_before_doing_it(runner, config_home, mocker):
    """The plan's own words: each command prints what it is about to do before it does it."""
    events = []
    mocker.patch("campaign_logger.bridge.shutil.which", return_value=SYSTEMCTL)
    mocker.patch("campaign_logger.bridge.write_units", side_effect=lambda *a: events.append("write") or [])
    mocker.patch("campaign_logger.bridge.systemctl", side_effect=lambda *a, **k: events.append(a[0]))
    mocker.patch("campaign_logger.bridge.click.echo", side_effect=lambda text: events.append(f"echo:{text}"))

    result = runner.invoke(main, ["bridge", "start"])

    assert result.exit_code == 0, result.output
    first_action = events.index("write")
    announced = " ".join(e for e in events[:first_action] if e.startswith("echo:"))
    assert "read-only" in announced
    assert f"{os.environ['XDG_RUNTIME_DIR']}/campaign-logger-mcp-ro/campaign-logger.sock" in announced
    assert events[first_action : first_action + 3] == ["write", "daemon-reload", "enable"]


def test_stop_disables(runner, config_home, fake_systemctl):
    result = runner.invoke(main, ["bridge", "stop"])

    assert result.exit_code == 0, result.output
    assert fake_systemctl == [[SYSTEMCTL, "--user", "disable", "--now", bridge.SOCKET_UNIT]]
    assert "Disabling" in result.output.splitlines()[0]


def test_status_reports_state_and_path(runner, config_home, fake_systemctl):
    result = runner.invoke(main, ["bridge", "status"])

    assert result.exit_code == 0, result.output
    assert fake_systemctl == [[SYSTEMCTL, "--user", "is-active", bridge.SOCKET_UNIT]]
    assert f"{bridge.SOCKET_UNIT}: active" in result.output
    assert f"{os.environ['XDG_RUNTIME_DIR']}/campaign-logger-mcp-ro/campaign-logger.sock" in result.output


@pytest.mark.parametrize("command", ["start", "stop", "status"])
def test_without_systemctl_exits_non_zero_with_one_line(runner, config_home, mocker, command):
    mocker.patch("campaign_logger.bridge.shutil.which", return_value=None)
    run = mocker.patch("campaign_logger.bridge.subprocess.run")

    result = runner.invoke(main, ["bridge", command])

    assert result.exit_code != 0
    assert len(result.output.strip().splitlines()) == 1
    assert "systemctl not found" in result.output
    run.assert_not_called()
    assert not (config_home / "systemd").exists()


def test_failing_systemctl_surfaces_its_first_line(runner, config_home, mocker):
    mocker.patch("campaign_logger.bridge.shutil.which", return_value=SYSTEMCTL)
    mocker.patch(
        "campaign_logger.bridge.subprocess.run",
        return_value=subprocess.CompletedProcess([], 1, stdout="", stderr="Failed to connect to bus: No medium found\nmore\n"),
    )

    result = runner.invoke(main, ["bridge", "stop"])

    assert result.exit_code != 0
    assert "systemctl --user disable --now campaign-logger-bridge.socket failed: Failed to connect to bus: No medium found" in result.output


def test_failing_systemctl_with_no_output_names_the_status(mocker):
    mocker.patch("campaign_logger.bridge.shutil.which", return_value=SYSTEMCTL)
    mocker.patch("campaign_logger.bridge.subprocess.run", return_value=subprocess.CompletedProcess([], 3, stdout="", stderr=""))
    with pytest.raises(bridge.BridgeError, match="exit status 3"):
        bridge.systemctl("daemon-reload")


# --- the socket directory ---------------------------------------------------


@POSIX_ONLY
def test_start_creates_the_socket_directory_private(runner, runtime_dir, fake_systemctl):
    result = runner.invoke(main, ["bridge", "start"])

    assert result.exit_code == 0, result.output
    directory = runtime_dir / bridge.SOCKET_DIR
    assert directory.is_dir()
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700


@POSIX_ONLY
def test_an_existing_directory_of_ours_is_tightened(runtime_dir):
    directory = runtime_dir / bridge.SOCKET_DIR
    directory.mkdir()
    directory.chmod(0o755)

    assert bridge.ensure_socket_dir() == directory
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700


@POSIX_ONLY
def test_a_directory_owned_by_someone_else_stops_start_with_one_line(runner, config_home, runtime_dir, fake_systemctl, mocker):
    """The owner's machine: Docker had made the directory ``root:root 0755`` (#168)."""
    directory = runtime_dir / bridge.SOCKET_DIR
    directory.mkdir()
    directory.chmod(0o755)
    mocker.patch("campaign_logger.bridge.os.getuid", return_value=directory.stat().st_uid + 1)

    result = runner.invoke(main, ["bridge", "start"])

    assert result.exit_code != 0
    error = [line for line in result.output.splitlines() if line.startswith("Error:")]
    assert len(error) == 1
    assert f"{directory} is owned by uid {directory.stat().st_uid}" in error[0]
    assert "Remove it" in error[0]
    assert "Writing" not in result.output and "Enabling" not in result.output
    assert stat.S_IMODE(directory.stat().st_mode) == 0o755, "someone else's directory must be left as it was"
    assert fake_systemctl == []
    assert not (config_home / "systemd").exists()


@POSIX_ONLY
@pytest.mark.skipif(os.name == "posix" and os.geteuid() == 0, reason="root can create anywhere")
def test_a_directory_that_cannot_be_created_stops_start_with_one_line(runner, config_home, tmp_path, fake_systemctl, monkeypatch):
    locked = tmp_path / "locked-run"
    locked.mkdir()
    locked.chmod(0o500)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(locked))
    try:
        result = runner.invoke(main, ["bridge", "start"])
    finally:
        locked.chmod(0o700)

    assert result.exit_code != 0
    assert f"Error: cannot create {locked / bridge.SOCKET_DIR}: Permission denied" in result.output
    assert fake_systemctl == []
    assert not (config_home / "systemd").exists()


def assert_refused_before_acting(result, config_home, fake_systemctl, message):
    """One ``Error:`` line naming the problem, nothing announced, no unit written, no systemctl call."""
    assert result.exit_code != 0
    assert len(result.output.strip().splitlines()) == 1, result.output
    assert result.output.startswith("Error:")
    assert message in result.output
    assert "Writing" not in result.output and "Enabling" not in result.output
    assert not (config_home / "systemd").exists()
    assert fake_systemctl == []


def test_a_file_in_the_way_is_refused(runner, config_home, runtime_dir, fake_systemctl):
    (runtime_dir / bridge.SOCKET_DIR).write_text("")
    result = runner.invoke(main, ["bridge", "start"])
    assert_refused_before_acting(result, config_home, fake_systemctl, "exists and is not a directory")


@POSIX_ONLY
def test_a_symlink_in_the_way_is_refused(runner, config_home, runtime_dir, fake_systemctl, tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir(mode=0o755)
    (runtime_dir / bridge.SOCKET_DIR).symlink_to(elsewhere)
    result = runner.invoke(main, ["bridge", "start"])
    assert_refused_before_acting(result, config_home, fake_systemctl, "exists and is not a directory")
    assert stat.S_IMODE(elsewhere.stat().st_mode) == 0o755, "the symlink's target must not be touched"


@POSIX_ONLY
@pytest.mark.skipif(os.name == "posix" and os.geteuid() == 0, reason="root can open anything")
def test_a_directory_that_cannot_be_opened_is_refused(runner, config_home, runtime_dir, fake_systemctl):
    directory = runtime_dir / bridge.SOCKET_DIR
    directory.mkdir()
    directory.chmod(0o000)
    try:
        result = runner.invoke(main, ["bridge", "start"])
    finally:
        directory.chmod(0o700)
    assert_refused_before_acting(result, config_home, fake_systemctl, f"cannot open {directory}: Permission denied")


def test_no_runtime_dir_is_refused(runner, config_home, fake_systemctl, monkeypatch):
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    result = runner.invoke(main, ["bridge", "start"])
    assert_refused_before_acting(result, config_home, fake_systemctl, "XDG_RUNTIME_DIR is not set")


def test_a_leftover_socket_file_stops_start_with_one_line(runner, config_home, runtime_dir, mocker):
    """The hand-run socat bridge used this same directory and socket name."""
    mocker.patch("campaign_logger.bridge.shutil.which", return_value=SYSTEMCTL)
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 3, stdout="inactive\n", stderr="")

    mocker.patch("campaign_logger.bridge.subprocess.run", side_effect=run)
    directory = runtime_dir / bridge.SOCKET_DIR
    directory.mkdir(mode=0o700)
    leftover = directory / bridge.SOCKET_NAME
    leftover.write_text("")

    result = runner.invoke(main, ["bridge", "start"])

    assert result.exit_code != 0
    assert len(result.output.strip().splitlines()) == 1, result.output
    assert f"{leftover} already exists and {bridge.SOCKET_UNIT} is not serving it" in result.output
    assert "systemctl --user stop campaign-logger-mcp-ro" in result.output
    assert leftover.exists(), "a socket that may be in use is never deleted"
    assert calls == [[SYSTEMCTL, "--user", "is-active", bridge.SOCKET_UNIT]]
    assert not (config_home / "systemd").exists()


def test_start_again_over_its_own_socket_proceeds(runner, config_home, runtime_dir, fake_systemctl):
    directory = runtime_dir / bridge.SOCKET_DIR
    directory.mkdir(mode=0o700)
    (directory / bridge.SOCKET_NAME).write_text("")

    result = runner.invoke(main, ["bridge", "start"])

    assert result.exit_code == 0, result.output
    assert fake_systemctl == [
        [SYSTEMCTL, "--user", "is-active", bridge.SOCKET_UNIT],
        [SYSTEMCTL, "--user", "daemon-reload"],
        [SYSTEMCTL, "--user", "enable", "--now", bridge.SOCKET_UNIT],
    ]


def test_bridge_is_registered_on_the_main_cli(runner):
    result = runner.invoke(main, ["bridge", "--help"])
    assert result.exit_code == 0
    for command in ("start", "stop", "status"):
        assert command in result.output


# --- over a real socket, with a stand-in for systemd ------------------------


class StandInSocket:
    """Accept connections like ``Accept=yes``: one ``ExecStart`` process per connection."""

    def __init__(self, path: Path, argv: list[str], env: dict[str, str]):
        """Listen at ``path`` with mode ``0600`` and serve ``argv`` per connection."""
        self.argv = argv
        self.env = env
        self.processes: list[subprocess.Popen] = []
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(str(path))
        os.chmod(path, 0o600)
        self.listener.listen()
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        while True:
            try:
                conn, _ = self.listener.accept()
            except OSError:
                return
            with conn:
                self.processes.append(
                    subprocess.Popen(self.argv, stdin=conn.fileno(), stdout=conn.fileno(), stderr=subprocess.DEVNULL, env=self.env)  # nosec B603
                )

    def close(self):
        """Stop accepting and end every server process."""
        self.listener.close()
        for process in self.processes:
            process.terminate()
            process.wait(timeout=10)


class LineClient:
    """A minimal MCP client speaking newline-delimited JSON-RPC, as the stdio transport does."""

    def __init__(self, path: Path):
        """Connect to the socket at ``path``."""
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(60)
        self.sock.connect(str(path))
        self.reader = self.sock.makefile("r", encoding="utf-8")
        self.next_id = 0

    def _write(self, message: dict) -> None:
        self.sock.sendall((json.dumps({"jsonrpc": "2.0", **message}) + "\n").encode())

    def notify(self, method: str) -> None:
        """Send a notification, which gets no reply."""
        self._write({"method": method})

    def request(self, method: str, params: dict | None = None) -> dict:
        """Send one request and return its reply."""
        self.next_id += 1
        message: dict = {"method": method, "id": self.next_id}
        if params is not None:
            message["params"] = params
        self._write(message)
        while True:
            reply = json.loads(self.reader.readline())
            if reply.get("id") == self.next_id:
                return reply

    def close(self):
        """Close the connection."""
        self.reader.close()
        self.sock.close()


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX") or sys.platform == "win32", reason="unix sockets and fd inheritance")
def test_read_tool_works_over_the_socket_and_write_tools_are_absent(monkeypatch):
    exe = shutil.which("campaign-logger")
    if exe is None:
        pytest.skip("campaign-logger is not installed on PATH")
    exec_start = next(x for x in bridge.render_service(exe).splitlines() if x.startswith("ExecStart="))
    argv = shlex.split(exec_start.removeprefix("ExecStart="))
    assert argv[-1] == "mcp"

    env = {k: v for k, v in os.environ.items() if not k.startswith("CL_")}
    # A short base keeps the socket path inside the 104-byte limit macOS imposes.
    base = Path(tempfile.mkdtemp(prefix="clb", dir="/tmp"))  # nosec B108 - mkdtemp: unique name, mode 0700, created atomically
    try:
        # The directory is the one ``bridge start`` creates, not one this test makes.
        monkeypatch.setenv("XDG_RUNTIME_DIR", str(base))
        directory = bridge.ensure_socket_dir()
        path = directory / bridge.SOCKET_NAME
        stand_in = StandInSocket(path, argv, env)
        try:
            assert stat.S_IMODE(directory.stat().st_mode) == 0o700
            assert stat.S_IMODE(path.stat().st_mode) == 0o600

            client = LineClient(path)
            try:
                init = client.request(
                    "initialize",
                    {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test-bridge", "version": "0"}},
                )
                assert "result" in init, init
                client.notify("notifications/initialized")

                tools = {t["name"] for t in client.request("tools/list")["result"]["tools"]}
                assert "get_tag_types" in tools
                for write_tool in ("create_campaign", "update_log_entry", "delete_campaign_entry"):
                    assert write_tool not in tools
                assert not {t for t in tools if t.startswith(("create_", "update_", "delete_"))}

                called = client.request("tools/call", {"name": "get_tag_types", "arguments": {}})["result"]
                assert not called.get("isError"), called
                assert json.loads(called["content"][0]["text"])["scope"] == "campaign-logger-defaults"

                refused = client.request("tools/call", {"name": "create_campaign", "arguments": {"name": "x"}})
                assert "error" in refused or refused["result"].get("isError"), refused
            finally:
                client.close()
        finally:
            stand_in.close()
    finally:
        shutil.rmtree(base, ignore_errors=True)


# --- write mode: a separate pair, opt-in (plan 167 unit 02) -----------------

EXE = "/opt/cl/bin/campaign-logger"

#: Unit 01's rendered text, written out in full. Write mode must not change a byte of it.
READ_SOCKET_UNIT_TEXT = """\
[Unit]
Description=Campaign Logger read-only MCP bridge for sandboxed agents

[Socket]
ListenStream=%t/campaign-logger-mcp-ro/campaign-logger.sock
SocketMode=0600
DirectoryMode=0700
RemoveOnStop=yes
Accept=yes

[Install]
WantedBy=sockets.target
"""

READ_SERVICE_UNIT_TEXT = """\
[Unit]
Description=Campaign Logger read-only MCP server for one bridge connection

[Service]
ExecStart=/opt/cl/bin/campaign-logger mcp
StandardInput=socket
StandardOutput=socket
StandardError=journal
"""


def test_the_read_units_are_byte_identical_to_unit_01s():
    assert bridge.render_socket() == READ_SOCKET_UNIT_TEXT
    assert bridge.render_service(EXE) == READ_SERVICE_UNIT_TEXT
    assert bridge.render_socket(bridge.READ) == READ_SOCKET_UNIT_TEXT
    assert bridge.render_service(EXE, bridge.READ) == READ_SERVICE_UNIT_TEXT


def test_the_write_socket_has_a_directory_of_its_own():
    """A sandbox mounts a socket's directory, so the write socket must never share the read one's."""
    assert bridge.WRITE_SOCKET_DIR != bridge.SOCKET_DIR
    assert bridge.WRITE.socket_dir == "campaign-logger-mcp-rw"
    assert "/" not in bridge.WRITE_SOCKET_DIR
    assert bridge.WRITE.socket_relative != bridge.READ.socket_relative
    assert os.path.dirname(bridge.WRITE.socket_relative) != os.path.dirname(bridge.READ.socket_relative)
    assert bridge.WRITE.socket_unit != bridge.READ.socket_unit
    assert bridge.WRITE.service_unit != bridge.READ.service_unit


def test_the_write_units_name_the_write_socket_and_run_the_write_server():
    socket_text = bridge.render_socket(bridge.WRITE)
    assert "ListenStream=%t/campaign-logger-mcp-rw/campaign-logger-write.sock\n" in socket_text
    assert "SocketMode=0600\n" in socket_text
    assert "DirectoryMode=0700\n" in socket_text
    assert "Accept=yes\n" in socket_text
    assert "RemoveOnStop=yes\n" in socket_text
    assert "campaign-logger-mcp-ro" not in socket_text

    service_text = bridge.render_service(EXE, bridge.WRITE)
    exec_lines = [line for line in service_text.splitlines() if line.startswith("ExecStart=")]
    assert exec_lines == [f"ExecStart={EXE} mcp --write"]
    assert exec_lines[0].endswith("mcp --write")
    assert "StandardInput=socket\n" in service_text
    assert "StandardOutput=socket\n" in service_text
    assert "--write" not in bridge.render_service(EXE), "only the write service may pass --write"


def test_the_write_units_carry_no_credential():
    text = bridge.render_socket(bridge.WRITE) + bridge.render_service(EXE, bridge.WRITE)
    for forbidden in ("Environment", "CL_", "token", "secret", "client"):
        assert forbidden not in text


def test_write_units_are_written_beside_the_read_units_without_touching_them(tmp_path):
    bridge.write_units(tmp_path, EXE)
    read_before = {name: (tmp_path / name).read_text() for name in (bridge.SOCKET_UNIT, bridge.SERVICE_UNIT)}

    written = bridge.write_units(tmp_path, EXE, bridge.WRITE)

    assert {p.name for p in written} == {bridge.WRITE_SOCKET_UNIT, bridge.WRITE_SERVICE_UNIT}
    assert {name: (tmp_path / name).read_text() for name in read_before} == read_before


def systemctl_units(calls):
    """The unit names every recorded ``systemctl`` call names."""
    return {arg for call in calls for arg in call if arg.startswith("campaign-logger-bridge")}


def test_start_without_write_never_names_a_write_unit(runner, config_home, fake_systemctl):
    result = runner.invoke(main, ["bridge", "start"])

    assert result.exit_code == 0, result.output
    assert systemctl_units(fake_systemctl) == {bridge.SOCKET_UNIT}
    assert not any("write" in " ".join(call) for call in fake_systemctl)
    assert not (config_home / "systemd" / "user" / bridge.WRITE_SOCKET_UNIT).exists()
    assert not (config_home / "systemd" / "user" / bridge.WRITE_SERVICE_UNIT).exists()


def test_stop_without_write_never_names_a_write_unit(runner, config_home, fake_systemctl):
    assert runner.invoke(main, ["bridge", "stop"]).exit_code == 0
    assert systemctl_units(fake_systemctl) == {bridge.SOCKET_UNIT}


def test_start_write_makes_the_expected_calls_on_the_write_unit_only(runner, config_home, runtime_dir, fake_systemctl):
    result = runner.invoke(main, ["bridge", "start", "--write"])

    assert result.exit_code == 0, result.output
    assert fake_systemctl == [
        [SYSTEMCTL, "--user", "daemon-reload"],
        [SYSTEMCTL, "--user", "enable", "--now", bridge.WRITE_SOCKET_UNIT],
    ]
    unit_dir = config_home / "systemd" / "user"
    assert (unit_dir / bridge.WRITE_SOCKET_UNIT).read_text() == bridge.render_socket(bridge.WRITE)
    assert (unit_dir / bridge.WRITE_SERVICE_UNIT).read_text() == bridge.render_service(bridge.executable(), bridge.WRITE)
    assert not (unit_dir / bridge.SOCKET_UNIT).exists(), "a --write command never writes the read pair"
    assert not (unit_dir / bridge.SERVICE_UNIT).exists()
    assert not (runtime_dir / bridge.SOCKET_DIR).exists(), "a --write command never creates the read directory"


@POSIX_ONLY
def test_start_write_creates_its_own_directory_private(runner, runtime_dir, fake_systemctl):
    assert runner.invoke(main, ["bridge", "start", "--write"]).exit_code == 0
    directory = runtime_dir / bridge.WRITE_SOCKET_DIR
    assert directory.is_dir()
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700


def test_stop_write_disables_the_write_unit_only(runner, config_home, fake_systemctl):
    result = runner.invoke(main, ["bridge", "stop", "--write"])

    assert result.exit_code == 0, result.output
    assert fake_systemctl == [[SYSTEMCTL, "--user", "disable", "--now", bridge.WRITE_SOCKET_UNIT]]
    assert f"{os.environ['XDG_RUNTIME_DIR']}/campaign-logger-mcp-rw/campaign-logger-write.sock" in result.output


def test_start_write_says_what_it_does_before_the_first_systemctl_call(runner, config_home, mocker):
    """No prompt (a supervisor may call this): the printed line is the disclosure, and it comes first."""
    events = []
    mocker.patch("campaign_logger.bridge.shutil.which", return_value=SYSTEMCTL)
    mocker.patch("campaign_logger.bridge.write_units", side_effect=lambda *a: events.append("write") or [])
    mocker.patch("campaign_logger.bridge.systemctl", side_effect=lambda *a, **k: events.append(f"systemctl:{a[0]}"))
    mocker.patch("campaign_logger.bridge.click.echo", side_effect=lambda text: events.append(f"echo:{text}"))

    result = runner.invoke(main, ["bridge", "start", "--write"])

    assert result.exit_code == 0, result.output
    first_systemctl = next(i for i, e in enumerate(events) if e.startswith("systemctl:"))
    first_write = events.index("write")
    disclosure = " ".join(e for e in events[:first_systemctl] if e.startswith("echo:"))
    assert f"{os.environ['XDG_RUNTIME_DIR']}/campaign-logger-mcp-rw/campaign-logger-write.sock" in disclosure
    assert "create, update and delete campaign data" in disclosure
    assert "your credentials" in disclosure
    assert events[first_write : first_write + 3] == ["write", "systemctl:daemon-reload", "systemctl:enable"]


def test_start_write_is_refused_for_a_leftover_socket_without_naming_the_hand_run_bridge(runner, config_home, runtime_dir, mocker):
    mocker.patch("campaign_logger.bridge.shutil.which", return_value=SYSTEMCTL)
    mocker.patch(
        "campaign_logger.bridge.subprocess.run",
        return_value=subprocess.CompletedProcess([], 3, stdout="inactive\n", stderr=""),
    )
    directory = runtime_dir / bridge.WRITE_SOCKET_DIR
    directory.mkdir(mode=0o700)
    (directory / bridge.WRITE_SOCKET_NAME).write_text("")

    result = runner.invoke(main, ["bridge", "start", "--write"])

    assert result.exit_code != 0
    assert f"{bridge.WRITE_SOCKET_UNIT} is not serving it" in result.output
    assert "campaign-logger bridge start --write" in result.output
    assert "campaign-logger-mcp-ro" not in result.output
    assert not (config_home / "systemd").exists()


def test_status_reports_both_sockets_labelled(runner, config_home, runtime_dir, mocker):
    """An open write socket is never hidden: with units installed, both are asked about and both are shown."""
    mocker.patch("campaign_logger.bridge.shutil.which", return_value=SYSTEMCTL)
    states = {bridge.SOCKET_UNIT: "active\n", bridge.WRITE_SOCKET_UNIT: "inactive\n"}
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout=states[command[-1]], stderr="")

    mocker.patch("campaign_logger.bridge.subprocess.run", side_effect=run)
    (config_home / "systemd" / "user").mkdir(parents=True)
    (config_home / "systemd" / "user" / bridge.WRITE_SOCKET_UNIT).write_text("")

    result = runner.invoke(main, ["bridge", "status"])

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines.index("read-only:") < lines.index("read-write:")
    assert f"{bridge.SOCKET_UNIT}: active" in lines
    assert f"{bridge.WRITE_SOCKET_UNIT}: inactive" in lines
    assert f"socket: {os.environ['XDG_RUNTIME_DIR']}/campaign-logger-mcp-ro/campaign-logger.sock" in lines
    assert f"socket: {os.environ['XDG_RUNTIME_DIR']}/campaign-logger-mcp-rw/campaign-logger-write.sock" in lines
    assert calls == [[SYSTEMCTL, "--user", "is-active", bridge.SOCKET_UNIT], [SYSTEMCTL, "--user", "is-active", bridge.WRITE_SOCKET_UNIT]]


def test_status_with_nothing_installed_still_names_the_write_socket_without_asking_systemd(runner, config_home, fake_systemctl):
    result = runner.invoke(main, ["bridge", "status"])

    assert result.exit_code == 0, result.output
    assert f"{bridge.WRITE_SOCKET_UNIT}: not installed" in result.output
    assert "campaign-logger-mcp-rw/campaign-logger-write.sock" in result.output
    assert fake_systemctl == [[SYSTEMCTL, "--user", "is-active", bridge.SOCKET_UNIT]]


def test_status_asks_about_a_write_socket_whose_unit_file_was_deleted(runner, config_home, runtime_dir, fake_systemctl):
    directory = runtime_dir / bridge.WRITE_SOCKET_DIR
    directory.mkdir(mode=0o700)
    (directory / bridge.WRITE_SOCKET_NAME).write_text("")

    result = runner.invoke(main, ["bridge", "status"])

    assert result.exit_code == 0, result.output
    assert f"{bridge.WRITE_SOCKET_UNIT}: active" in result.output
    assert [SYSTEMCTL, "--user", "is-active", bridge.WRITE_SOCKET_UNIT] in fake_systemctl


def test_status_write_reports_only_the_write_socket(runner, config_home, fake_systemctl):
    result = runner.invoke(main, ["bridge", "status", "--write"])

    assert result.exit_code == 0, result.output
    assert fake_systemctl == [[SYSTEMCTL, "--user", "is-active", bridge.WRITE_SOCKET_UNIT]]
    assert f"{bridge.WRITE_SOCKET_UNIT}: active" in result.output
    assert f"{bridge.SOCKET_UNIT}:" not in result.output


@pytest.mark.parametrize("command", ["start", "stop", "status"])
def test_write_commands_without_systemctl_exit_non_zero_with_one_line(runner, config_home, mocker, command):
    mocker.patch("campaign_logger.bridge.shutil.which", return_value=None)
    run = mocker.patch("campaign_logger.bridge.subprocess.run")

    result = runner.invoke(main, ["bridge", command, "--write"])

    assert result.exit_code != 0
    assert result.output.strip().splitlines() == [
        "Error: systemctl not found: the bridge needs a systemd user manager, and there is no fallback."
    ]
    run.assert_not_called()


def test_there_is_no_way_to_start_the_write_socket_or_widen_the_read_one_without_the_flag(runner, config_home, fake_systemctl):
    """No default, no upgrade path: only ``--write`` names the write pair, and the read service never says ``--write``."""
    for args in (["start"], ["stop"], ["status"]):
        runner.invoke(main, ["bridge", *args])
    assert bridge.WRITE_SOCKET_UNIT not in {arg for call in fake_systemctl if call[2] in ("enable", "start") for arg in call}
    assert "--write" not in bridge.render_service(bridge.executable())
    params = {p.name for command in bridge.bridge.commands.values() for p in command.params}
    assert params == {"write"}, "no config option or environment-variable switch is added"


# --- write mode over real sockets, with a stand-in for systemd ----------------

#: Launches the real server with the Logger API replaced by a stub, as ``campaign-logger`` would be launched.
STUB_LAUNCHER = """\
import sys
from unittest import mock

class Created:
    def model_dump_json(self, indent=None):
        return '{"id": "stub-campaign", "title": "from the stub"}'

class StubLoggerClient:
    def __init__(self, client_id=None, client_secret=None):
        pass

    def create_campaign(self, title, description=""):
        return Created()

with mock.patch("campaign_logger.mcp_server.LoggerClient", StubLoggerClient), mock.patch("campaign_logger.mcp_server.load_config"):
    from campaign_logger.cli import main
    main(sys.argv[1:], prog_name="campaign-logger")
"""


def initialised(path: Path) -> LineClient:
    client = LineClient(path)
    init = client.request(
        "initialize",
        {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test-bridge", "version": "0"}},
    )
    assert "result" in init, init
    client.notify("notifications/initialized")
    return client


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX") or sys.platform == "win32", reason="unix sockets and fd inheritance")
def test_the_write_socket_lists_write_tools_and_a_write_call_works_while_the_read_socket_still_has_none(tmp_path, monkeypatch):
    launcher = tmp_path / "launcher.py"
    launcher.write_text(STUB_LAUNCHER)

    def argv_for(mode: bridge.Mode) -> list[str]:
        """The rendered ``ExecStart``, with this installation's script swapped for the API-stubbing launcher."""
        exec_start = next(x for x in bridge.render_service(EXE, mode).splitlines() if x.startswith("ExecStart="))
        rendered = shlex.split(exec_start.removeprefix("ExecStart="))
        assert rendered[0] == EXE
        return [sys.executable, str(launcher), *rendered[1:]]

    assert argv_for(bridge.WRITE)[2:] == ["mcp", "--write"]
    assert argv_for(bridge.READ)[2:] == ["mcp"]

    env = {k: v for k, v in os.environ.items() if not k.startswith("CL_")}
    env.update({"CL_LOGGER_CLIENT_ID": "stub-id", "CL_LOGGER_CLIENT_SECRET": "stub-secret"})  # nosec B105 - a stub value for a fake client, not a credential
    base = Path(tempfile.mkdtemp(prefix="clb", dir="/tmp"))  # nosec B108 - mkdtemp: unique name, mode 0700, created atomically
    try:
        monkeypatch.setenv("XDG_RUNTIME_DIR", str(base))
        read_dir = bridge.ensure_socket_dir(bridge.READ)
        write_dir = bridge.ensure_socket_dir(bridge.WRITE)
        assert read_dir != write_dir
        read_path = read_dir / bridge.SOCKET_NAME
        write_path = write_dir / bridge.WRITE_SOCKET_NAME
        read_stand_in = StandInSocket(read_path, argv_for(bridge.READ), env)
        write_stand_in = StandInSocket(write_path, argv_for(bridge.WRITE), env)
        try:
            for directory, path in ((read_dir, read_path), (write_dir, write_path)):
                assert stat.S_IMODE(directory.stat().st_mode) == 0o700
                assert stat.S_IMODE(path.stat().st_mode) == 0o600

            write_client = initialised(write_path)
            try:
                write_tools = {t["name"] for t in write_client.request("tools/list")["result"]["tools"]}
                assert {"create_campaign", "update_campaign", "delete_campaign"} <= write_tools
                assert "get_tag_types" in write_tools, "the write server serves the read tools too"

                created = write_client.request("tools/call", {"name": "create_campaign", "arguments": {"title": "from the test"}})["result"]
                assert not created.get("isError"), created
                assert "Campaign created successfully" in created["content"][0]["text"]
                assert "stub-campaign" in created["content"][0]["text"]
            finally:
                write_client.close()

            read_client = initialised(read_path)
            try:
                read_tools = {t["name"] for t in read_client.request("tools/list")["result"]["tools"]}
                assert "get_tag_types" in read_tools
                assert not {t for t in read_tools if t.startswith(("create_", "update_", "delete_"))}
                assert read_tools < write_tools
                refused = read_client.request("tools/call", {"name": "create_campaign", "arguments": {"title": "x"}})
                assert "error" in refused or refused["result"].get("isError"), refused
            finally:
                read_client.close()
        finally:
            write_stand_in.close()
            read_stand_in.close()
    finally:
        shutil.rmtree(base, ignore_errors=True)
