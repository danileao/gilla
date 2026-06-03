import json
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from devex_cli.main import app

runner = CliRunner()


def test_pr_create_mock_mode():
    with patch("devex_cli.commands.pr.Repo") as mock_repo:
        mock_repo.return_value.active_branch.name = "LOG-987-delivery-pipeline"

        result = runner.invoke(app, ["pr-create", "--mock"])
        assert result.exit_code == 0
        assert "Running in MOCK mode" in result.output
        assert "SOC 2" in result.output


def test_pr_create_mock_without_soc2():
    with patch("devex_cli.commands.pr.Repo") as mock_repo:
        mock_repo.return_value.active_branch.name = "FIN-001-feature"

        result = runner.invoke(app, ["pr-create", "--mock"])
        assert result.exit_code == 0
        assert "[FIN-001]" in result.output


def test_pr_create_mock_with_reviewers():
    with patch("devex_cli.commands.pr.Repo") as mock_repo:
        mock_repo.return_value.active_branch.name = "FIN-001-feature"

        result = runner.invoke(app, ["pr-create", "--mock", "--reviewer", "alice", "--reviewer", "bob"])
        assert result.exit_code == 0
        assert "alice, bob" in result.output


@patch("devex_cli.commands.pr.os.getenv")
@patch("devex_cli.commands.pr.urllib.request.urlopen")
@patch("devex_cli.commands.pr.Repo")
def test_pr_create_real_api_success(mock_repo, mock_urlopen, mock_getenv):
    mock_getenv.return_value = "ghp_mock_token_secret"
    mock_repo.return_value.active_branch.name = "BNK-456-credit-card"
    mock_repo.return_value.remotes.origin.url = "git@github.com:platform/repo.git"

    mock_ref = MagicMock()
    mock_ref.name = "origin/main"
    mock_repo.return_value.remotes.origin.refs = [mock_ref]

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "html_url": "https://github.com/platform/repo/pull/42",
        "number": 42
    }).encode("utf-8")

    mock_reviewer_response = MagicMock()
    mock_reviewer_response.read.return_value = b"{}"

    mock_urlopen.side_effect = [
        MagicMock(__enter__=MagicMock(return_value=mock_response)),
        MagicMock(__enter__=MagicMock(return_value=mock_reviewer_response)),
    ]

    result = runner.invoke(app, ["pr-create", "--reviewer", "alice", "--reviewer", "bob"])
    assert result.exit_code == 0
    assert "Pull Request successfully created" in result.output
    assert "reviewer(s) successfully requested" in result.output


@patch("devex_cli.commands.pr.os.getenv")
@patch("devex_cli.commands.pr.urllib.request.urlopen")
@patch("devex_cli.commands.pr.Repo")
def test_pr_create_real_api_with_master_base(mock_repo, mock_urlopen, mock_getenv):
    mock_getenv.return_value = "ghp_mock_token_secret"
    mock_repo.return_value.active_branch.name = "BNK-456-credit-card"
    mock_repo.return_value.remotes.origin.url = "git@github.com:platform/repo.git"

    mock_ref_main = MagicMock()
    mock_ref_main.name = "origin/master"
    mock_repo.return_value.remotes.origin.refs = [mock_ref_main]

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "html_url": "https://github.com/platform/repo/pull/42",
        "number": 42
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    result = runner.invoke(app, ["pr-create"])
    assert result.exit_code == 0
    assert "Pull Request successfully created" in result.output


@patch("devex_cli.commands.pr.os.getenv")
@patch("devex_cli.commands.pr.Repo")
def test_pr_create_missing_token_error(mock_repo, mock_getenv):
    mock_getenv.return_value = None
    mock_repo.return_value.active_branch.name = "FIN-111-invoice"
    mock_repo.return_value.remotes.origin.url = "git@github.com:owner/repo.git"

    result = runner.invoke(app, ["pr-create"])
    assert result.exit_code == 1


def test_pr_create_gitpython_missing():
    with patch("devex_cli.commands.pr.Repo", None):
        result = runner.invoke(app, ["pr-create", "--mock"])
        assert result.exit_code == 1
        assert "gitpython" in result.output


def test_pr_create_on_main_branch():
    with patch("devex_cli.commands.pr.Repo") as mock_repo:
        mock_repo.return_value.active_branch.name = "main"

        result = runner.invoke(app, ["pr-create", "--mock"])
        assert result.exit_code == 1
        assert "main" in result.output


def test_pr_create_on_master_branch():
    with patch("devex_cli.commands.pr.Repo") as mock_repo:
        mock_repo.return_value.active_branch.name = "master"

        result = runner.invoke(app, ["pr-create", "--mock"])
        assert result.exit_code == 1
        assert "main" in result.output


def test_pr_create_non_compliant_branch():
    with patch("devex_cli.commands.pr.Repo") as mock_repo:
        mock_repo.return_value.active_branch.name = "random-branch"

        result = runner.invoke(app, ["pr-create", "--mock"])
        assert result.exit_code == 1
        assert "governance" in result.output.lower() or "violates" in result.output.lower()


@patch("devex_cli.commands.pr.os.getenv")
@patch("devex_cli.commands.pr.Repo")
def test_pr_create_http_error(mock_repo, mock_getenv):
    mock_getenv.return_value = "ghp_mock_token"
    mock_repo.return_value.active_branch.name = "FIN-111-invoice"
    mock_repo.return_value.remotes.origin.url = "git@github.com:owner/repo.git"
    mock_ref = MagicMock()
    mock_ref.name = "origin/main"
    mock_repo.return_value.remotes.origin.refs = [mock_ref]

    import urllib.error
    http_error = urllib.error.HTTPError(
        url="https://api.github.com/repos/owner/repo/pulls",
        code=422,
        msg="Unprocessable Entity",
        hdrs={},
        fp=None
    )
    http_error.read = lambda: b'{"message":"Validation failed"}'

    with patch("devex_cli.commands.pr.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = http_error

        result = runner.invoke(app, ["pr-create"])
        assert result.exit_code == 1
        assert "HTTP Error" in result.output


@patch("devex_cli.commands.pr.os.getenv")
@patch("devex_cli.commands.pr.Repo")
def test_pr_create_unexpected_error(mock_repo, mock_getenv):
    mock_getenv.return_value = "ghp_mock_token"
    mock_repo.return_value.active_branch.name = "FIN-111-invoice"
    mock_repo.return_value.remotes.origin.url = "git@github.com:owner/repo.git"
    mock_ref = MagicMock()
    mock_ref.name = "origin/main"
    mock_repo.return_value.remotes.origin.refs = [mock_ref]

    with patch("devex_cli.commands.pr.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = Exception("Connection refused")

        result = runner.invoke(app, ["pr-create"])
        assert result.exit_code == 1
        assert "Unexpected Error" in result.output
