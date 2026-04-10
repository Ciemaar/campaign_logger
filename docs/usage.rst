=====
Usage
=====

Campaign Logger provides both a Generator API and a Main App API.

Generator API
=============

The Generator API handles the creation and execution of random generators.

To use the Generator API in a project::

    from campaign_logger.api import GeneratorClient

    # Initialize client with your token
    client = GeneratorClient(token="your_api_token")

    # List generators
    generators = client.list_generators()
    for gen in generators:
        print(f"{gen.id}: {gen.name}")

    # Generate a result
    if generators:
        result = client.execute_operation(generators[0].id, "generate")
        print(result)

Generator CLI Usage
-------------------

The package includes a command-line interface `campaign-logger`.

Authentication for the Generator CLI can be provided via the ``--token`` option or by setting the ``CL_GENERATOR_TOKEN`` environment variable.

.. code-block:: bash

    export CL_GENERATOR_TOKEN="your_generator_api_token"

List generators::

    campaign-logger generator list

Get a specific generator::

    campaign-logger generator get <generator_id>

Generate a result::

    campaign-logger generator generate <generator_id>


Main Campaign Logger API (JSON:API)
===================================

The main Campaign Logger application exposes a JSON:API compliant REST API at ``https://logger.campaign-logger.com``.
You can use the ``LoggerClient`` to manage Campaigns, Logs, Log Entries, and Campaign Entries (Pages).

Authentication
--------------
You must pass your API token to the client. It will be sent in the `Authorization` header as a Bearer token.

Examples using ``LoggerClient``
-------------------------------

**Create a new Campaign:**

.. code-block:: python

    from campaign_logger.api import LoggerClient

    client = LoggerClient(client_id="your_client_id", client_secret="your_client_secret")

    response = client.create_campaign(
        title="My Epic Campaign",
        description="A new adventure begins."
    )
    campaign_id = response["data"]["id"]
    print(f"Created campaign with ID: {campaign_id}")


**Create a new Log within a Campaign:**

.. code-block:: python

    response = client.create_log(
        campaign_id=campaign_id,
        title="Session 1 Notes",
        description="The party meets in a tavern."
    )
    log_id = response["data"]["id"]
    print(f"Created log with ID: {log_id}")


**Create a new Log Entry:**

.. code-block:: python

    response = client.create_log_entry(
        log_id=log_id,
        raw_text="The mysterious stranger gives @Jack a map to ^The Lost Mine."
    )
    print("Created log entry successfully.")

**Update a Log Entry:**

.. code-block:: python

    response = client.update_log_entry(
        entry_id=entry_id,
        raw_text="The mysterious stranger gave @Jack a fake map."
    )
    print("Updated log entry successfully.")

**Delete a Log Entry:**

.. code-block:: python

    client.delete_log_entry(entry_id)


Logger CLI Usage
----------------

The ``logger`` command group provides management of the core entities.

Authentication for the Logger CLI can be provided via the ``--client-id`` and ``--client-secret`` options or by setting the ``CL_LOGGER_CLIENT_ID`` and ``CL_LOGGER_CLIENT_SECRET`` environment variables.

.. code-block:: bash

    export CL_LOGGER_CLIENT_ID="your_client_id"
    export CL_LOGGER_CLIENT_SECRET="your_client_secret"

Campaigns
^^^^^^^^^

.. code-block:: bash

    campaign-logger logger campaign list
    campaign-logger logger campaign get <id>
    campaign-logger logger campaign create "My Campaign" --description "Optional"
    campaign-logger logger campaign update <id> --title "New Title"
    campaign-logger logger campaign delete <id>

Logs
^^^^

.. code-block:: bash

    campaign-logger logger log list
    campaign-logger logger log get <id>
    campaign-logger logger log create <campaign_id> "Session 1"
    campaign-logger logger log update <id> --title "Session 1 - Revised"
    campaign-logger logger log delete <id>

Entries
^^^^^^^

.. code-block:: bash

    campaign-logger logger entry list
    campaign-logger logger entry get <id>
    campaign-logger logger entry create <log_id> "Some raw text here"
    campaign-logger logger entry update <id> "New text"
    campaign-logger logger entry delete <id>

Pages (Campaign Entries)
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    campaign-logger logger page list
    campaign-logger logger page get <id>
    campaign-logger logger page create <campaign_id> "Page text"
    campaign-logger logger page update <id> "Updated page text"
    campaign-logger logger page delete <id>
