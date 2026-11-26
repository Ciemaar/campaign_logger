=========================================
Model Context Protocol (MCP) Integration
=========================================

This project integrates with the Model Context Protocol (MCP) to provide an easy way to access the Campaign Logger functionalities directly from AI models and agents using standard MCP clients (like Claude Desktop).

Overview
========

The Model Context Protocol (MCP) is an open standard that enables AI models to interact with local or remote tools and resources securely. It standardizes the connection between models (clients) and data sources (servers).

In the context of the Campaign Logger CLI, the MCP integration runs a local server that exposes various actions (tools) which an AI client can execute on your behalf. For example, a model could be asked to:

- List all your campaigns
- Generate an encounter from a custom generator
- Add a new log entry directly to your campaign

How it works
============

The ``src/campaign_logger/mcp_server.py`` file contains the ``MCPServer`` implementation which wraps the ``LoggerClient`` and ``GeneratorClient``. The MCP standard defines several primitives; this project focuses specifically on **Tools**.

Tools
-----

Tools represent callable functions that the AI model can discover and use. We expose functions to interact with both the main Campaign Logger API and the Generator API:

* **Read-only tools (enabled by default):**

  * ``list_campaigns``, ``get_campaign``
  * ``list_logs``, ``get_log``
  * ``list_log_entries``, ``get_log_entry``
  * ``list_campaign_entries``, ``get_campaign_entry``
  * ``list_generators``, ``get_generator``, ``generate_result``

* **Write tools (enabled when read-only mode is off):**

  * ``create_campaign``, ``update_campaign``, ``delete_campaign``
  * ``create_log``, ``update_log``, ``delete_log``
  * ``create_log_entry``, ``update_log_entry``, ``delete_log_entry``
  * ``create_campaign_entry``, ``update_campaign_entry``, ``delete_campaign_entry``

Architecture Details
====================

We use the official Python SDK ``mcp``.

* We instantiate an ``MCPServer`` object (imported via ``from mcp.server.mcpserver import MCPServer``).
* We wrap existing Python functions with the ``@server.tool()`` decorator, allowing the server to automatically extract function signatures and types, exposing them as tools via the protocol.
* The standard handles standard input/output (``stdio``) mapping. When you run ``campaign-logger mcp``, the CLI listens on ``stdin`` for JSON-RPC messages defined by the protocol and outputs responses on ``stdout``.
* Note: It is very important that background debugging or unexpected prints do not happen when running in MCP mode, as any output outside of JSON-RPC protocol messages will disrupt communication with the MCP client.

Setup and Usage
===============

Prerequisites
-------------
Make sure your environment variables (or ``~/.campaign_logger.json`` config) are properly configured:

* ``CL_GENERATOR_TOKEN``
* ``CL_LOGGER_CLIENT_ID``
* ``CL_LOGGER_CLIENT_SECRET``

Running the Server
------------------

You can run the MCP server directly via the CLI:

.. code-block:: bash

    # Read-only mode (exposes only list/get/generate tools - default)
    campaign-logger mcp

    # Read-write mode (exposes create/update/delete tools)
    campaign-logger mcp --write

Integration with Claude Desktop
-------------------------------

To connect your AI assistant (e.g., Claude Desktop) to your Campaign Logger setup, you configure the client to run this CLI command.

For Claude Desktop, modify your ``claude_desktop_config.json``:

.. code-block:: json

    {
      "mcpServers": {
        "campaign-logger": {
          "command": "campaign-logger",
          "args": ["mcp"],
          "env": {
            "CL_GENERATOR_TOKEN": "your-token",
            "CL_LOGGER_CLIENT_ID": "your-id",
            "CL_LOGGER_CLIENT_SECRET": "your-secret"
          }
        }
      }
    }

Once running, the AI model will dynamically discover the configured tools, and you can prompt it:
*"What campaigns do I currently have in my Campaign Logger?"*

Bridge for sandboxes
====================

An agent in a sandbox cannot start ``campaign-logger mcp`` on your machine itself. The ``bridge`` commands let a systemd *user* service on your machine do it for the sandbox, over a unix socket. Campaign Logger is a structured database that helps plan roleplaying games, and the bridge only gives a sandboxed assistant access to the same MCP tools described above.

It needs a Linux systemd user session. On a machine without ``systemctl --user`` the commands exit with a one-line error and do nothing else.

What ``bridge start`` does
--------------------------

Read this before you run it. ``campaign-logger bridge start``:

#. creates the directory ``$XDG_RUNTIME_DIR/campaign-logger-mcp-ro`` (mode ``0700``), or checks the one that exists, and stops with one line if it belongs to someone else or something else is in the way;
#. writes two unit files into ``~/.config/systemd/user/`` (``$XDG_CONFIG_HOME/systemd/user/`` if that is set), only where they differ: ``campaign-logger-bridge.socket`` and ``campaign-logger-bridge@.service``;
#. runs ``systemctl --user daemon-reload`` and ``systemctl --user enable --now campaign-logger-bridge.socket``.

The socket listens at ``$XDG_RUNTIME_DIR/campaign-logger-mcp-ro/campaign-logger.sock`` (mode ``0600``). systemd starts one ``campaign-logger mcp`` per connection, using the path of the ``campaign-logger`` you ran ``bridge start`` with, and nothing runs between connections. No credential is written into a unit; the service runs as you and reads ``~/.campaign_logger.json`` like any other ``campaign-logger mcp``.

**Nothing starts by installing Campaign Logger, and nothing starts until you run** ``bridge start``. Once you have, the socket is *enabled*, so systemd starts it again at your next login until you run ``bridge stop``.

Read-only is the default
------------------------

The default socket serves ``campaign-logger mcp``, which has read tools only. The write tools are never registered on it, so a connected agent cannot see them, let alone call them. Nothing in ``bridge start`` can make this socket serve write tools.

Read-write is a separate socket
-------------------------------

``bridge start --write`` opens a second, independent socket for an agent that is allowed to change your data:

* **Socket:** ``$XDG_RUNTIME_DIR/campaign-logger-mcp-rw/campaign-logger-write.sock``, in a directory of its own (mode ``0700``, socket ``0600``).
* **Units:** ``campaign-logger-bridge-write.socket`` and ``campaign-logger-bridge-write@.service``, whose service runs ``campaign-logger mcp --write``.
* **What a connected agent can then do:** create, update and delete campaigns, logs, log entries and pages, using your credentials.

It is never started unless you name it: ``bridge start`` without ``--write`` does not touch it, and ``--write`` commands do not touch the read-only socket. ``bridge start --write`` prints the socket and what the agent can change before it does anything, and does not ask for confirmation. Like the read socket, once started it comes back at your next login until you run ``bridge stop --write``.

Each socket has its own directory because a sandbox mounts a socket's *directory*, not the socket. Mount only ``campaign-logger-mcp-ro`` and the sandbox can reach the read-only server and nothing else. Nothing mounts ``campaign-logger-mcp-rw`` unless you add it.

Checking it
-----------

.. code-block:: bash

    campaign-logger bridge status

This reports both sockets, labelled, and where each listens. A write socket that was never started is reported as ``not installed``. ``status --write`` reports only the write socket.

Connecting from the sandbox
---------------------------

Mount ``$XDG_RUNTIME_DIR/campaign-logger-mcp-ro`` into the sandbox read-only, then register this as the MCP server command, where ``<mount>`` is where the directory appears inside the sandbox:

.. code-block:: bash

    socat STDIO UNIX-CONNECT:<mount>/campaign-logger.sock

The mount, the registration and the allow rules belong to the sandbox tooling, which lives in the owner's AgenticRulesAndTools repository (``docs/sandbox_manual.md`` and ``docs/sandbox_example_agy_rpg.md``) and is not copied here. That repository is private, so there is no link. Its pages may still name an older host directory for the socket; use the paths on this page.

Removing it
-----------

#. ``campaign-logger bridge stop`` disables and stops the read-only socket, and removes its socket file. For the write socket run ``campaign-logger bridge stop --write``.
#. ``bridge stop`` leaves the unit files in place. To remove them, delete the two read-only units from ``~/.config/systemd/user/`` (``campaign-logger-bridge.socket`` and ``campaign-logger-bridge@.service``), plus the two write units (``campaign-logger-bridge-write.socket`` and ``campaign-logger-bridge-write@.service``) if you ever started write mode.
#. Run ``systemctl --user daemon-reload``.
