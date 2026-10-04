lazy from click.testing import CliRunner

lazy from campaign_logger.cli import main


def test_main():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0  # nosec
    assert "Usage: main [OPTIONS] COMMAND [ARGS]..." in result.output  # nosec
