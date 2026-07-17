def pytest_addoption(parser):
    """Registers a custom command-line option `--run-e2e` with pytest.

    This allows developers to explicitly opt-in to running slow, network-dependent end-to-end tests.
    """
    parser.addoption("--run-e2e", action="store_true", default=False, help="run live end-to-end tests")


def pytest_configure(config):
    """Registers the `e2e` custom marker with pytest to prevent 'unknown marker' warnings.

    This marker is used to tag tests that interact with live external services.
    """
    config.addinivalue_line("markers", "e2e: mark test as a live end-to-end test")


def pytest_collection_modifyitems(config, items):
    """Skip end-to-end tests unless explicitly requested via --run-e2e.

    This ensures local dev and standard CI runs are fast and don't require external network access
    or live API keys unless specifically testing integration with live servers.
    """
    if config.getoption("--run-e2e"):
        # --run-e2e given in cli: do not skip e2e tests
        return
    import pytest

    skip_e2e = pytest.mark.skip(reason="need --run-e2e option to run")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)
