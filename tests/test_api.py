import secrets

import pytest
import requests_mock

from campaign_logger.api import GeneratorClient
from campaign_logger.models import GeneratorModel

BASE_URL = "https://generator.campaign-logger.com"


@pytest.fixture
def client():
    return GeneratorClient(base_url=BASE_URL, token=secrets.token_hex(16))


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
        assert len(generators) == 2  # nosec
        assert generators[0].id == "gen1"  # nosec
        assert generators[1].name == "Generator 2"  # nosec

        m.get(
            f"{BASE_URL}/api2/generators",
            json={
                "generators": [
                    {"id": "gen1", "name": "Generator 1"},
                    {"id": "gen2", "name": "Generator 2"},
                ]
            },
        )
        generators = client.list_generators()
        assert len(generators) == 2  # nosec
        assert generators[0].id == "gen1"  # nosec
        assert generators[1].name == "Generator 2"  # nosec


def test_get_generator(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/api2/generators/gen1", json={"id": "gen1", "name": "Generator 1"})
        generator = client.get_generator("gen1")
        assert generator.id == "gen1"  # nosec
        assert generator.name == "Generator 1"  # nosec

        m.get(f"{BASE_URL}/api2/generators/gen2", json={"generators": [{"id": "gen2", "name": "Generator 2"}]})
        generator = client.get_generator("gen2")
        assert generator.id == "gen2"  # nosec
        assert generator.name == "Generator 2"  # nosec


def test_get_generator_by_name(client):
    with requests_mock.Mocker() as m:
        m.get(
            f"{BASE_URL}/api2/generators",
            json=[
                {"id": "gen1", "name": "Generator 1"},
                {"id": "gen2", "name": "Generator 2"},
            ],
        )
        generator = client.get_generator_by_name("Generator 2")
        assert generator is not None
        assert generator.id == "gen2"
        assert generator.name == "Generator 2"

        generator = client.get_generator_by_name("Nonexistent Generator")
        assert generator is None


def test_create_generator(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/api2/generators", json={"id": "new_gen", "name": "New Generator"})
        model = GeneratorModel(id="new_gen", name="New Generator")  # pyright: ignore
        created = client.create_generator(model)
        assert created.id == "new_gen"  # nosec
        assert created.name == "New Generator"  # nosec

        m.post(f"{BASE_URL}/api2/generators", json={"generators": [{"id": "new_gen_2", "name": "New Generator 2"}]})
        created = client.create_generator(model)
        assert created.id == "new_gen_2"  # nosec
        assert created.name == "New Generator 2"  # nosec


def test_update_generator(client):
    with requests_mock.Mocker() as m:
        m.put(
            f"{BASE_URL}/api2/generators/gen1",
            json={"id": "gen1", "name": "Updated Generator"},
        )
        model = GeneratorModel(id="gen1", name="Updated Generator")  # pyright: ignore
        updated = client.update_generator("gen1", model)
        assert updated.name == "Updated Generator"  # nosec

        m.put(
            f"{BASE_URL}/api2/generators/gen1",
            json={"generators": [{"id": "gen1", "name": "Updated Generator 2"}]},
        )
        updated = client.update_generator("gen1", model)
        assert updated.name == "Updated Generator 2"  # nosec


def test_delete_generator(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/api2/generators/gen1", status_code=200)
        client.delete_generator("gen1")
        assert m.called  # nosec


def test_generator_model_methods(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/api2/generators/validate", status_code=200)
        model = GeneratorModel(id="gen1", name="Test")  # pyright: ignore
        model._client = client
        model.validate_generator()
        assert m.called

        m.post(f"{BASE_URL}/api2/generators/generate", json={"result": "random result"})
        result = model.generate()
        assert result == {"result": "random result"}

        m.put(f"{BASE_URL}/api2/generators/gen1", json={"id": "gen1", "name": "Saved Generator"})
        saved = model.save()
        assert saved.name == "Saved Generator"

        m.delete(f"{BASE_URL}/api2/generators/gen1", status_code=200)
        model.delete()
        assert m.called

        model_no_id = GeneratorModel(name="No ID")  # pyright: ignore
        model_no_id._client = client
        with pytest.raises(ValueError):
            model_no_id.save()
        with pytest.raises(ValueError):
            model_no_id.delete()


def test_validate_generator(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/api2/generators/validate", status_code=200)
        model = GeneratorModel(id="gen1", name="Test")  # pyright: ignore
        client.validate_generator(model)
        assert m.called  # nosec


def test_generate_random(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/api2/generators/generate", json={"result": "random result"})
        model = GeneratorModel(id="gen1", name="Test")  # pyright: ignore
        result = client.generate(model)
        assert result == {"result": "random result"}  # nosec


def test_execute_operation(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/api2/generators/gen1/generate", json={"result": "executed"})
        result = client.execute_operation("gen1", "generate")
        assert result == {"result": "executed"}  # nosec

    with pytest.raises(ValueError):
        client.execute_operation("gen1", "invalid_operation")


def test_get_execute_tokens(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/api2/generators/gen1/execute-tokens", json=["token1", "token2"])
        tokens = client.get_execute_tokens("gen1")
        assert len(tokens) == 2  # nosec
        assert "token1" in tokens  # nosec


def test_create_execute_token(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/api2/generators/gen1/execute-tokens", json="new_token")
        token = client.create_execute_token("gen1")
        assert token == "new_token"  # nosec


def test_delete_execute_token(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/api2/generators/gen1/execute-tokens/token1", status_code=200)
        client.delete_execute_token("gen1", "token1")
        assert m.called  # nosec
