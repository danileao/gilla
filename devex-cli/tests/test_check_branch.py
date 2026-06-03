import pytest
from typer.testing import CliRunner
from unittest.mock import patch
from devex_cli.main import app

runner = CliRunner()


def test_check_branch_compliant():
    with patch("devex_cli.commands.check_branch.Path.exists") as mock_exists, \
         patch("devex_cli.commands.check_branch.Repo") as mock_repo:
        mock_exists.return_value = True
        mock_repo.return_value.active_branch.name = "FIN-123-secure-checkout"

        result = runner.invoke(app, ["check-branch"])
        assert result.exit_code == 0
        assert "válida para o Work ID" in result.output


def test_check_branch_non_compliant():
    with patch("devex_cli.commands.check_branch.Path.exists") as mock_exists, \
         patch("devex_cli.commands.check_branch.Repo") as mock_repo:
        mock_exists.return_value = True
        mock_repo.return_value.active_branch.name = "just-a-random-branch"

        result = runner.invoke(app, ["check-branch"])
        assert result.exit_code == 1
        assert "Erro de Governança" in result.output


def test_check_branch_bypass_main():
    with patch("devex_cli.commands.check_branch.Path.exists") as mock_exists, \
         patch("devex_cli.commands.check_branch.Repo") as mock_repo:
        mock_exists.return_value = True
        mock_repo.return_value.active_branch.name = "main"

        result = runner.invoke(app, ["check-branch"])
        assert result.exit_code == 0
        assert "Ignorando validação" in result.output


def test_check_branch_bypass_master():
    with patch("devex_cli.commands.check_branch.Path.exists") as mock_exists, \
         patch("devex_cli.commands.check_branch.Repo") as mock_repo:
        mock_exists.return_value = True
        mock_repo.return_value.active_branch.name = "master"

        result = runner.invoke(app, ["check-branch"])
        assert result.exit_code == 0
        assert "Ignorando validação" in result.output


def test_check_branch_bypass_development():
    with patch("devex_cli.commands.check_branch.Path.exists") as mock_exists, \
         patch("devex_cli.commands.check_branch.Repo") as mock_repo:
        mock_exists.return_value = True
        mock_repo.return_value.active_branch.name = "development"

        result = runner.invoke(app, ["check-branch"])
        assert result.exit_code == 0
        assert "Ignorando validação" in result.output


def test_check_branch_bypass_dev():
    with patch("devex_cli.commands.check_branch.Path.exists") as mock_exists, \
         patch("devex_cli.commands.check_branch.Repo") as mock_repo:
        mock_exists.return_value = True
        mock_repo.return_value.active_branch.name = "dev"

        result = runner.invoke(app, ["check-branch"])
        assert result.exit_code == 0
        assert "Ignorando validação" in result.output


def test_check_branch_no_git_dir():
    with patch("devex_cli.commands.check_branch.Path.exists") as mock_exists:
        mock_exists.return_value = False

        result = runner.invoke(app, ["check-branch"])
        assert result.exit_code == 0
        assert "precisa ser usado dentro" in result.output or "needs to be used inside" in result.output


def test_check_branch_gitpython_missing():
    with patch("devex_cli.commands.check_branch.Path.exists") as mock_exists, \
         patch("devex_cli.commands.check_branch.Repo", None):
        mock_exists.return_value = True

        result = runner.invoke(app, ["check-branch"])
        assert result.exit_code == 1
        assert "gitpython" in result.output


def test_check_branch_generic_exception():
    with patch("devex_cli.commands.check_branch.Path.exists") as mock_exists, \
         patch("devex_cli.commands.check_branch.Repo") as mock_repo:
        mock_exists.return_value = True
        mock_repo.side_effect = Exception("some unexpected error")

        result = runner.invoke(app, ["check-branch"])
        assert result.exit_code == 1
        assert "Erro ao ler" in result.output
