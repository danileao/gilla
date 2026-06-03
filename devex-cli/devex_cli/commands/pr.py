import os
import re
import typer
import urllib.request
import json
from pathlib import Path
from rich.console import Console
from devex_cli.constants import WORK_ID_REGEX
from devex_cli.commands.validate import _run_validation

try:
    from git import Repo
except ImportError:
    Repo = None

console = Console()

DEFAULT_PR_TEMPLATE = """## 📋 Descrição
{WORK_ID}: **Descreva suas alterações aqui**

## 🔄 Tipo de Mudança
- [ ] Nova Feature
- [ ] Correção de Bug
- [ ] Refatoração
- [ ] Documentação
- [ ] Atualização de Dependência

## ✅ Testes
- [ ] Testes Unitários
- [ ] Testes de Integração
- [ ] Testes Manuais

## 🔐 Governance & Audit Trail (SOC 2)
- **Work ID:** {WORK_ID}
- **Two-Reviewer Rule:** OBRIGATÓRIO
- **Time:** {TEAM_OWNER}
- **Aprovações Necessárias:** {REQUIRED_APPROVALS}
"""


def _load_pr_body(work_id: str, team_owner: str = "N/A", required_approvals: str = "2") -> str:
    template_path = Path(".github/PULL_REQUEST_TEMPLATE.md")
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        template = DEFAULT_PR_TEMPLATE

    return template.replace("{WORK_ID}", work_id).replace(
        "{TEAM_OWNER}", team_owner
    ).replace("{REQUIRED_APPROVALS}", required_approvals)


def _load_devex_config() -> dict:
    config_path = Path("devex.json")
    if config_path.exists():
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def pr_create(
    mock: bool = typer.Option(False, "--mock", help="Run in mock mode without remote interactions"),
    reviewer: list[str] = typer.Option([], "--reviewer", help="GitHub usernames to request as reviewers (can be used multiple times)"),
    title: str = typer.Option("", "--title", help="Custom PR title (default: uses Work ID)")
):
    """[PLUS] Creates a REAL Pull Request on GitHub using Git metadata and GitHub API Token"""
    try:
        if Repo is None:
            raise Exception("'gitpython' library is missing.")

        repo = Repo(".")
        if repo.head.is_detached:
            console.print("[red]❌ Error:[/red] Cannot create a Pull Request with detached HEAD. Switch to a feature branch first.")
            raise typer.Exit(code=1)

        current_branch = repo.active_branch.name

        if current_branch in ["main", "master"]:
            console.print("[red]❌ Error:[/red] You cannot submit a Pull Request directly from 'main'.")
            raise typer.Exit(code=1)

        match = re.match(WORK_ID_REGEX, current_branch)
        if not match:
            console.print(f"[red]❌ Error:[/red] Current branch '{current_branch}' violates core platform governance rules.")
            raise typer.Exit(code=1)

        work_id = match.group(0)
        devex_config = _load_devex_config()
        governance = devex_config.get("governance", {})
        team_owner = governance.get("teamOwner", "N/A")
        required_approvals = str(governance.get("requiredApprovals", "2"))
        pr_title = title if title else f"[{work_id}] Automated Contribution via DevEx Golden Path CLI"
        pr_body = _load_pr_body(work_id, team_owner, required_approvals)

        if mock:
            console.print("[blue]ℹ Running in MOCK mode (Dry-Run)...[/blue]")
            console.print(f"[bold blue]PR Title:[/bold blue] {pr_title}\n{pr_body}")
            if reviewer:
                console.print(f"[yellow]👥 Requested Reviewers:[/yellow] {', '.join(reviewer)}")
            raise typer.Exit(code=0)

        console.print("\n[yellow]🔍 Running Shift-Left validation before creating PR...[/yellow]")
        if not _run_validation():
            console.print("[red]❌ PR creation aborted due to validation failures.[/red]")
            raise typer.Exit(code=1)

        console.print("[green]✔ Shift-Left validation passed, proceeding with PR creation...[/green]\n")

        remote_url = repo.remotes.origin.url
        url_clean = remote_url.replace("git@github.com:", "").replace("https://github.com/", "").replace(".git", "")

        token = os.getenv("GITHUB_TOKEN")
        if not token:
            console.print("[red]❌ Error:[/red] GITHUB_TOKEN environment variable is not set.")
            raise typer.Exit(code=1)

        console.print("[yellow]🚀 Pushing current branch to remote origin...[/yellow]")
        repo.git.push('origin', current_branch)

        remote_refs = [ref.name for ref in repo.remotes.origin.refs]
        target_base = "main"
        if "origin/main" not in remote_refs and "origin/master" in remote_refs:
            target_base = "master"

        console.print(f"[yellow]📦 Dispatching request to GitHub API v3 (Target Base: {target_base})...[/yellow]")

        api_url = f"https://api.github.com/repos/{url_clean}/pulls"
        payload = {
            "title": pr_title,
            "body": pr_body,
            "head": current_branch,
            "base": target_base,
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        }

        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            pr_number = res_data.get("number")
            console.print("[green]✔ Pull Request successfully created on GitHub via Token![/green]")
            console.print(f"[blue]🔗 PR Link:[/blue] {res_data.get('html_url')}")

        if reviewer:
            console.print(f"[yellow]👥 Requesting reviewers: {', '.join(reviewer)}...[/yellow]")
            reviewer_url = f"{api_url}/{pr_number}/requested_reviewers"
            reviewer_payload = {"reviewers": reviewer}
            reviewer_req = urllib.request.Request(
                reviewer_url,
                data=json.dumps(reviewer_payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(reviewer_req) as reviewer_resp:
                reviewer_resp.read()
            console.print(f"[green]✔ {len(reviewer)} reviewer(s) successfully requested![/green]")
        else:
            console.print("[yellow]⚠ No reviewers specified. Use --reviewer flag to request reviewers.[/yellow]")
        raise typer.Exit(code=0)

    except typer.Exit:
        raise
    except urllib.error.HTTPError as e:
        console.print(f"[red]❌ GitHub API HTTP Error:[/red] {e.code} - {e.reason}")
        console.print(f"[yellow]Details:[/yellow] {e.read().decode('utf-8')}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected Error packaging Pull Request:[/red] {str(e)}")
        raise typer.Exit(code=1)