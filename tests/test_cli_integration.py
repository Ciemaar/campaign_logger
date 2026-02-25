import pytest
from click.testing import CliRunner
from campaign_logger.cli import main
from unittest.mock import MagicMock
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
        FullGeneratorModel(id="1", name="Gen 1"),
        FullGeneratorModel(id="2", name="Gen 2")
    ]
    mock_instance.get_generator.return_value = FullGeneratorModel(id="1", name="Gen 1")
    mock_instance.create_generator.return_value = FullGeneratorModel(id="3", name="New Gen")
    mock_instance.update_generator.return_value = FullGeneratorModel(id="1", name="Updated Gen")
    mock_instance.generate_random.return_value = {"result": "random"}
    mock_instance.execute_operation.return_value = {"result": "op result"}

    # Patch the class in cli.py so it returns our mock instance
    mocker.patch('campaign_logger.cli.GeneratorClient', return_value=mock_instance)

    return mock_instance

def test_list_generators(runner, mock_client):
    result = runner.invoke(main, ['list'])
    assert result.exit_code == 0
    assert "1: Gen 1" in result.output
    assert "2: Gen 2" in result.output
    mock_client.list_generators.assert_called_once()

def test_get_generator(runner, mock_client):
    result = runner.invoke(main, ['get', '1'])
    assert result.exit_code == 0
    assert '"id": "1"' in result.output
    mock_client.get_generator.assert_called_once_with('1')

def test_create_generator(runner, mock_client):
    with runner.isolated_filesystem():
        with open('new.json', 'w') as f:
            f.write('{"name": "New Gen"}')
        result = runner.invoke(main, ['create', 'new.json'])
        assert result.exit_code == 0
        assert '"id": "3"' in result.output
        mock_client.create_generator.assert_called_once()

def test_update_generator(runner, mock_client):
    with runner.isolated_filesystem():
        with open('update.json', 'w') as f:
            f.write('{"name": "Updated Gen"}')
        result = runner.invoke(main, ['update', '1', 'update.json'])
        assert result.exit_code == 0
        assert '"name": "Updated Gen"' in result.output
        mock_client.update_generator.assert_called_once()

def test_delete_generator(runner, mock_client):
    result = runner.invoke(main, ['delete', '1'])
    assert result.exit_code == 0
    assert "Generator 1 deleted." in result.output
    mock_client.delete_generator.assert_called_once_with('1')

def test_generate_from_id(runner, mock_client):
    result = runner.invoke(main, ['generate', '1'])
    assert result.exit_code == 0
    assert '"result": "op result"' in result.output
    mock_client.execute_operation.assert_called_once_with('1', 'generate')

def test_validate_from_id(runner, mock_client):
    result = runner.invoke(main, ['validate', '1'])
    assert result.exit_code == 0
    assert "Generator 1 is valid." in result.output
    mock_client.execute_operation.assert_called_once_with('1', 'validate')
