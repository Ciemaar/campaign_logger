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

    # Read-write mode (exposes create/update/delete tools)
    campaign-logger mcp

    # Read-only mode (exposes only list/get/generate tools)
    campaign-logger mcp --read-only

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
