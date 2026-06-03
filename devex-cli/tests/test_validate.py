from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from devex_cli.main import app

runner = CliRunner()


def test_validate_no_devex_json():
    with patch("devex_cli.commands.validate.Path.exists") as mock_exists:
        mock_exists.return_value = False

        result = runner.invoke(app, ["validate"])
        assert result.exit_code == 0
        assert "No build steps" in result.output


def test_validate_empty_build_steps():
    with patch("devex_cli.commands.validate.Path.exists") as mock_exists, \
         patch("devex_cli.commands.validate.Path.read_text") as mock_read:
        mock_exists.return_value = True
        mock_read.return_value = '{"buildSteps": []}'

        result = runner.invoke(app, ["validate"])
        assert result.exit_code == 0
        assert "No build steps" in result.output


def test_validate_all_steps_pass():
    with patch("devex_cli.commands.validate.Path.exists") as mock_exists, \
         patch("devex_cli.commands.validate.Path.read_text") as mock_read, \
         patch("devex_cli.commands.validate.subprocess.run") as mock_run:
        mock_exists.return_value = True
        mock_read.return_value = '{"buildSteps": ["echo ok"]}'
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["validate"])
        assert result.exit_code == 0
        assert "validations passed" in result.output


def test_validate_step_fails():
    with patch("devex_cli.commands.validate.Path.exists") as mock_exists, \
         patch("devex_cli.commands.validate.Path.read_text") as mock_read, \
         patch("devex_cli.commands.validate.subprocess.run") as mock_run:
        mock_exists.return_value = True
        mock_read.return_value = '{"buildSteps": ["failing-command"]}'
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: something broke"
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["validate"])
        assert result.exit_code == 1
        assert "FAILED" in result.output
