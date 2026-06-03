from typer.testing import CliRunner
from unittest.mock import patch
from devex_cli.main import app

runner = CliRunner()


def test_init_creates_hook_successfully():
    with patch("devex_cli.commands.init.Path.exists") as mock_exists, \
         patch("devex_cli.commands.init.Path.mkdir") as mock_mkdir, \
         patch("devex_cli.commands.init.Path.write_text") as mock_write, \
         patch("devex_cli.commands.init.Path.chmod") as mock_chmod:
        mock_exists.return_value = True

        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "installed successfully" in result.output
        mock_write.assert_called_once()
        mock_chmod.assert_called_once_with(0o755)


def test_init_no_git_dir():
    with patch("devex_cli.commands.init.Path.exists") as mock_exists:
        mock_exists.return_value = False

        result = runner.invoke(app, ["init"])
        assert result.exit_code == 1
        assert ".git" in result.output
        assert "not found" in result.output or "não encontrado" in result.output


def init_write_error_scenario(mock_write):
    mock_write.side_effect = PermissionError("Permission denied")


def test_init_write_permission_error():
    with patch("devex_cli.commands.init.Path.exists") as mock_exists, \
         patch("devex_cli.commands.init.Path.mkdir") as mock_mkdir, \
         patch("devex_cli.commands.init.Path.write_text") as mock_write, \
         patch("devex_cli.commands.init.Path.chmod") as mock_chmod:
        mock_exists.return_value = True
        mock_write.side_effect = PermissionError("Permission denied")

        result = runner.invoke(app, ["init"])
        assert result.exit_code == 1
        assert "Error" in result.output or "Erro" in result.output


def test_init_hooks_dir_already_exists():
    with patch("devex_cli.commands.init.Path.exists") as mock_exists, \
         patch("devex_cli.commands.init.Path.mkdir") as mock_mkdir, \
         patch("devex_cli.commands.init.Path.write_text") as mock_write, \
         patch("devex_cli.commands.init.Path.chmod") as mock_chmod:
        mock_exists.return_value = True

        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "installed successfully" in result.output
        mock_mkdir.assert_called_once_with(exist_ok=True)
