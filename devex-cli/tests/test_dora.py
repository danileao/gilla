import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from devex_cli.main import app

runner = CliRunner()


def test_dora_mock_mode_output():
    with patch("devex_cli.commands.dora._get_owner_repo_from_git") as mock_git:
        mock_git.return_value = ("fin", "transactionify-api")

        result = runner.invoke(app, ["dora", "--mock"])

        assert result.exit_code == 0
        assert "DORA Metrics" in result.output
        assert "fin/transactionify-api" in result.output
        assert "Deployment Frequency" in result.output
        assert "Lead Time" in result.output
        assert "Change Failure Rate" in result.output
        assert "MTTR" in result.output


def test_dora_mock_saves_json():
    with patch("devex_cli.commands.dora._get_owner_repo_from_git") as mock_git:
        mock_git.return_value = ("fin", "transactionify-api")

        result = runner.invoke(app, ["dora", "--mock"])

        assert result.exit_code == 0
        json_path = Path("dora-metrics.json")
        assert json_path.exists()
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert "deployment_frequency" in data
        assert "lead_time_median_hours" in data
        assert "change_failure_rate" in data
        assert "mttr_hours" in data
        assert data["owner"] == "fin"
        assert data["repo"] == "transactionify-api"
        json_path.unlink(missing_ok=True)


def test_dora_mock_with_custom_owner_repo():
    result = runner.invoke(app, ["dora", "--mock", "--owner", "myteam", "--repo", "myapp", "--days", "90"])

    assert result.exit_code == 0
    assert "myteam/myapp" in result.output
    assert "90d" in result.output or "90" in result.output


def test_dora_no_git_remote_and_no_flags():
    with patch("devex_cli.commands.dora._get_owner_repo_from_git") as mock_git:
        mock_git.return_value = None

        result = runner.invoke(app, ["dora", "--mock"])

        assert result.exit_code == 1
        assert "Could not infer" in result.output


def test_dora_real_api_success():
    with patch("devex_cli.commands.dora._get_owner_repo_from_git") as mock_git, \
         patch("devex_cli.commands.dora.os.getenv") as mock_getenv, \
         patch("devex_cli.commands.dora._make_github_request") as mock_api:

        mock_git.return_value = ("fin", "transactionify-api")
        mock_getenv.return_value = "ghp_mock_token"

        mock_api.side_effect = [
            [{"created_at": "2026-06-01T10:00:00Z", "status": "success"},
             {"created_at": "2026-05-28T10:00:00Z", "status": "success"}],
            {"default_branch": "main"},
            [{"created_at": "2026-05-20T08:00:00Z", "merged_at": "2026-05-20T12:00:00Z"},
             {"created_at": "2026-05-22T09:00:00Z", "merged_at": "2026-05-22T11:30:00Z"}],
            {"workflow_runs": [
                {"created_at": "2026-06-01T10:00:00Z", "conclusion": "success"},
                {"created_at": "2026-05-28T10:00:00Z", "conclusion": "failure"},
            ]},
        ]

        result = runner.invoke(app, ["dora"])

        assert result.exit_code == 0
        assert "DORA Metrics" in result.output


def test_dora_real_api_missing_token():
    with patch("devex_cli.commands.dora._get_owner_repo_from_git") as mock_git, \
         patch("devex_cli.commands.dora.os.getenv") as mock_getenv:

        mock_git.return_value = ("fin", "transactionify-api")
        mock_getenv.return_value = None

        result = runner.invoke(app, ["dora"])

        assert result.exit_code == 1
        assert "GITHUB_TOKEN" in result.output


def test_dora_benchmark_values():
    from devex_cli.commands.dora import _dora_benchmark

    assert _dora_benchmark(0.5, "deployment_frequency") == "Low"
    assert _dora_benchmark(5, "deployment_frequency") == "High"
    assert _dora_benchmark(0.5, "lead_time") == "Elite (<1h)"
    assert _dora_benchmark(200, "lead_time") == "Low (>=1w)"
    assert _dora_benchmark(0, "cfr") == "Elite (0-5%)"
    assert _dora_benchmark(0.5, "cfr") == "Low (>15%)"
