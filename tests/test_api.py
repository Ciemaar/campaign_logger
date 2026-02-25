import pytest
import requests_mock

from campaign_logger.api import GeneratorClient
from campaign_logger.models import FullGeneratorModel

BASE_URL = "https://generator.campaign-logger.com"


@pytest.fixture
def client():
    return GeneratorClient(base_url=BASE_URL, token="fake_token")


def test_list_generators(client):
    with requests_mock.Mocker() as m:
        m.get(
            f"{BASE_URL}/api2/generators",
            json=[
                {"id": "gen1", "name": "Generator 1"},
                {"id": "gen2", "name": "Generator 2"},
            ],
        )
        generators = client.list_generators()
        assert len(generators) == 2
        assert generators[0].id == "gen1"
        assert generators[1].name == "Generator 2"


def test_get_generator(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/api2/generators/gen1", json={"id": "gen1", "name": "Generator 1"})
        generator = client.get_generator("gen1")
        assert generator.id == "gen1"
        assert generator.name == "Generator 1"


def test_create_generator(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/api2/generators", json={"id": "new_gen", "name": "New Generator"})
        model = FullGeneratorModel(id="new_gen", name="New Generator")  # pyright: ignore
        created = client.create_generator(model)
        assert created.id == "new_gen"
        assert created.name == "New Generator"


def test_update_generator(client):
    with requests_mock.Mocker() as m:
        m.put(
            f"{BASE_URL}/api2/generators/gen1",
            json={"id": "gen1", "name": "Updated Generator"},
        )
        model = FullGeneratorModel(id="gen1", name="Updated Generator")  # pyright: ignore
        updated = client.update_generator("gen1", model)
        assert updated.name == "Updated Generator"


def test_delete_generator(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/api2/generators/gen1", status_code=200)
        client.delete_generator("gen1")
        assert m.called


def test_validate_generator(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/api2/generators/validate", status_code=200)
        model = FullGeneratorModel(id="gen1", name="Test")  # pyright: ignore
        client.validate_generator(model)
        assert m.called


def test_generate_random(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/api2/generators/generate", json={"result": "random result"})
        model = FullGeneratorModel(id="gen1", name="Test")  # pyright: ignore
        result = client.generate_random(model)
        assert result == {"result": "random result"}


def test_execute_operation(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/api2/generators/gen1/generate", json={"result": "executed"})
        result = client.execute_operation("gen1", "generate")
        assert result == {"result": "executed"}


def test_get_execute_tokens(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/api2/generators/gen1/execute-tokens", json=["token1", "token2"])
        tokens = client.get_execute_tokens("gen1")
        assert len(tokens) == 2
        assert "token1" in tokens


def test_create_execute_token(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/api2/generators/gen1/execute-tokens", json="new_token")
        token = client.create_execute_token("gen1")
        assert token == "new_token"


def test_delete_execute_token(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/api2/generators/gen1/execute-tokens/token1", status_code=200)
        client.delete_execute_token("gen1", "token1")
        assert m.called
