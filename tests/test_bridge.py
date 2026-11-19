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
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1000")
    return home


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
    assert "ListenStream=%t/agent-sandbox/mcp/campaign-logger.sock\n" in text
    assert "SocketMode=0600\n" in text
    assert "DirectoryMode=0700\n" in text
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
    assert bridge.socket_path() == "$XDG_RUNTIME_DIR/agent-sandbox/mcp/campaign-logger.sock"


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
    assert (unit_dir / bridge.SOCKET_UNIT).read_text() == bridge.render_socket()
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
    assert "/run/user/1000/agent-sandbox/mcp/campaign-logger.sock" in announced
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
    assert "/run/user/1000/agent-sandbox/mcp/campaign-logger.sock" in result.output


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
def test_read_tool_works_over_the_socket_and_write_tools_are_absent():
    exe = shutil.which("campaign-logger")
    if exe is None:
        pytest.skip("campaign-logger is not installed on PATH")
    exec_start = next(x for x in bridge.render_service(exe).splitlines() if x.startswith("ExecStart="))
    argv = shlex.split(exec_start.removeprefix("ExecStart="))
    assert argv[-1] == "mcp"

    env = {k: v for k, v in os.environ.items() if not k.startswith("CL_")}
    # A short base keeps the socket path inside the 104-byte limit macOS imposes.
    base = Path(tempfile.mkdtemp(prefix="clb", dir="/tmp"))
    try:
        directory = base / "agent-sandbox" / "mcp"
        directory.mkdir(parents=True, mode=0o700)
        os.chmod(base / "agent-sandbox", 0o700)
        os.chmod(directory, 0o700)
        path = directory / "campaign-logger.sock"
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
