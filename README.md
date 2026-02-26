# campaign_logger

Python interface to Campaign Logger.

This library provides a Python client and CLI for the [Campaign Logger Generator API](https://generator.campaign-logger.com/).

## Features

- **API Client:** `GeneratorClient` class to interact with Generator API endpoints.
- **CLI Tool:** `campaign-logger` command-line interface for managing generators.
- **Data Models:** Pydantic models for type-safe interaction with API data structures.

## Installation

```bash
pip install campaign-logger
```

## CLI Usage

The CLI tool allows you to list, get, create, update, delete, generate, and validate generators.

```bash
# Set your API token (or use --token option)
export CL_GENERATOR_TOKEN="your_api_token"

# List all generators
campaign-logger list

# Get a generator by ID
campaign-logger get <generator_id>

# Generate a result
campaign-logger generate <generator_id>
```

See the [documentation](https://campaign_logger.readthedocs.io/) for more details.
