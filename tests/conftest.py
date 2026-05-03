def pytest_addoption(parser):
    parser.addoption("--run-e2e", action="store_true", default=False, help="run live end-to-end tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: mark test as a live end-to-end test")


def pytest_collection_modifyitems(config, items):
    pass
