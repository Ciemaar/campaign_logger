from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from campaign_logger.cli import main
from campaign_logger.models import FullGeneratorModel


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_client(mocker):
    # Create a mock instance of GeneratorClient
    mock_instance = MagicMock()

    # Configure default returns
    mock_instance.list_generators.return_value = [
        FullGeneratorModel(id="1", name="Gen 1"),  # pyright: ignore
        FullGeneratorModel(id="2", name="Gen 2"),  # pyright: ignore
    ]
    mock_instance.get_generator.return_value = FullGeneratorModel(id="1", name="Gen 1")  # pyright: ignore
    mock_instance.create_generator.return_value = FullGeneratorModel(id="3", name="New Gen")  # pyright: ignore
    mock_instance.update_generator.return_value = FullGeneratorModel(id="1", name="Updated Gen")  # pyright: ignore
    mock_instance.generate_random.return_value = {"result": "random"}
    mock_instance.execute_operation.return_value = {"result": "op result"}

    # Patch the class in cli.py so it returns our mock instance
    mocker.patch("campaign_logger.cli.GeneratorClient", return_value=mock_instance)

    return mock_instance


def test_list_generators(runner, mock_client):
    result = runner.invoke(main, ["generator", "list"])
    assert result.exit_code == 0  # nosec
    assert "1: Gen 1" in result.output  # nosec
    assert "2: Gen 2" in result.output  # nosec
    mock_client.list_generators.assert_called_once()


def test_get_generator(runner, mock_client):
    result = runner.invoke(main, ["generator", "get", "1"])
    assert result.exit_code == 0  # nosec
    assert '"id": "1"' in result.output  # nosec
    mock_client.get_generator.assert_called_once_with("1")


def test_create_generator(runner, mock_client):
    with runner.isolated_filesystem():
        with open("new.json", "w") as f:
            f.write('{"name": "New Gen"}')
        result = runner.invoke(main, ["generator", "create", "new.json"])
        assert result.exit_code == 0  # nosec
        assert '"id": "3"' in result.output  # nosec
        mock_client.create_generator.assert_called_once()


def test_update_generator(runner, mock_client):
    with runner.isolated_filesystem():
        with open("update.json", "w") as f:
            f.write('{"name": "Updated Gen"}')
        result = runner.invoke(main, ["generator", "update", "1", "update.json"])
        assert result.exit_code == 0  # nosec
        assert '"name": "Updated Gen"' in result.output  # nosec
        mock_client.update_generator.assert_called_once()


def test_delete_generator(runner, mock_client):
    result = runner.invoke(main, ["generator", "delete", "1"])
    assert result.exit_code == 0  # nosec
    assert "Generator 1 deleted." in result.output  # nosec
    mock_client.delete_generator.assert_called_once_with("1")


def test_generate_from_id(runner, mock_client):
    result = runner.invoke(main, ["generator", "generate", "1"])
    assert result.exit_code == 0  # nosec
    assert '"result": "op result"' in result.output  # nosec
    mock_client.execute_operation.assert_called_once_with("1", "generate")


def test_validate_from_id(runner, mock_client):
    result = runner.invoke(main, ["generator", "validate", "1"])
    assert result.exit_code == 0  # nosec
    assert "Generator 1 is valid." in result.output  # nosec
    mock_client.execute_operation.assert_called_once_with("1", "validate")


def test_generator_cli_error_handling(runner, mock_client):
    mock_client.list_generators.side_effect = Exception("API is down")
    result = runner.invoke(main, ["generator", "list"])
    assert result.exit_code == 0  # click's default behavior for caught errors here
    assert "Error: API is down" in result.output  # nosec

    mock_client.get_generator.side_effect = Exception("Not found")
    result = runner.invoke(main, ["generator", "get", "1"])
    assert "Error: Not found" in result.output  # nosec

    with runner.isolated_filesystem():
        with open("new.json", "w") as f:
            f.write('{"name": "New Gen"}')
        mock_client.create_generator.side_effect = Exception("Create failed")
        result = runner.invoke(main, ["generator", "create", "new.json"])
        assert "Error: Create failed" in result.output  # nosec

        mock_client.update_generator.side_effect = Exception("Update failed")
        result = runner.invoke(main, ["generator", "update", "1", "new.json"])
        assert "Error: Update failed" in result.output  # nosec

    mock_client.delete_generator.side_effect = Exception("Delete failed")
    result = runner.invoke(main, ["generator", "delete", "1"])
    assert "Error: Delete failed" in result.output  # nosec

    mock_client.execute_operation.side_effect = Exception("Generate failed")
    result = runner.invoke(main, ["generator", "generate", "1"])
    assert "Error: Generate failed" in result.output  # nosec

    mock_client.execute_operation.side_effect = Exception("Validate failed")
    result = runner.invoke(main, ["generator", "validate", "1"])
    assert "Error: Validate failed" in result.output  # nosec
