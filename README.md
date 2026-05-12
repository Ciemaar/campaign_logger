# campaign_logger

Python interface to Campaign Logger.

This library provides a Python client and CLI for the
[Campaign Logger Generator API](https://generator.campaign-logger.com/). It also
documents usage for the main
[Campaign Logger JSON:API](https://logger.campaign-logger.com/).

## Features

- **Generator API Client:** `GeneratorClient` class to interact with Generator
  API endpoints.
- **Generator CLI Tool:** `campaign-logger` command-line interface for managing
  generators.
- **Data Models:** Pydantic models for type-safe interaction with API data
  structures.

## Installation

```bash
pip install campaign-logger
```

## Development Setup

To set up a local development environment, clone the repository and install the
package with testing dependencies:

```bash
git clone https://github.com/Ciemaar/campaign_logger.git
cd campaign_logger

# Create and activate a virtual environment using standard tools
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[test]"

# Alternatively, using uv for faster installation
uv venv
source .venv/bin/activate
uv pip install -e ".[test]"
```

Run tests across environments using `tox`:

```bash
tox
```

## CLI Usage (Generators)

The CLI tool allows you to list, get, create, update, delete, generate, and
validate generators.

```bash
# Set your API token (or use --token option)
export CL_GENERATOR_TOKEN="your_api_token"

# List all generators
campaign-logger generator list

# Get a generator by ID
campaign-logger get <generator_id>

# Generate a result
campaign-logger generate <generator_id>
```

## Main App API Usage (Campaigns, Logs, Entries)

The main app uses a JSON:API specification. Here is a brief example using
`requests`:

```python
import requests

headers = {
    "api-client": "your_client_id",
    "api-secret": "your_client_secret",
    "Content-Type": "application/vnd.api+json",
    "Accept": "application/vnd.api+json"
}

# Create a Campaign
payload = {
    "data": {
        "type": "campaigns",
        "attributes": {
            "title": "My Epic Campaign",
            "description": "A new adventure begins."
        }
    }
}
response = requests.post("https://logger.campaign-logger.com/campaigns", headers=headers, json=payload)
print(response.json())
```

See the [documentation](https://campaign_logger.readthedocs.io/) for more
details and examples on Logs and Log Entries.
