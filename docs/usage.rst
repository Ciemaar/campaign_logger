=====
Usage
=====

To use Campaign Logger in a project::

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

CLI Usage
=========

The package includes a command-line interface `campaign-logger`.

List generators::

    campaign-logger list

Get a specific generator::

    campaign-logger get <generator_id>

Generate a result::

    campaign-logger generate <generator_id>

Authentication
--------------

You can provide authentication credentials via command-line options or environment variables:

- ``--token`` or ``CL_GENERATOR_TOKEN``
- ``--client-id`` or ``CL_GENERATOR_CLIENT_ID``
- ``--client-secret`` or ``CL_GENERATOR_CLIENT_SECRET``
