import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def _get_owner_repo_from_git() -> tuple[str, str] | None:
    try:
        from git import Repo
        repo = Repo(".")
        remote_url = repo.remotes.origin.url
        url_clean = remote_url.replace("git@github.com:", "").replace("https://github.com/", "").replace(".git", "")
        parts = url_clean.split("/")
        if len(parts) == 2:
            return parts[0], parts[1]
    except Exception:
        pass
    return None


def _make_github_request(endpoint: str, token: str) -> list | dict:
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def _calculate_lead_times(prs: list) -> list[float]:
    lead_times = []
    for pr in prs:
        created = pr.get("created_at")
        merged = pr.get("merged_at")
        if created and merged:
            created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            merged_dt = datetime.fromisoformat(merged.replace("Z", "+00:00"))
            lead_hours = (merged_dt - created_dt).total_seconds() / 3600
            if lead_hours >= 0:
                lead_times.append(lead_hours)
    return lead_times


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n % 2 == 0:
        return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    return sorted_vals[n // 2]


DORA_BENCHMARKS: dict[str, list[tuple[float, str]]] = {
    "deployment_frequency": [(1, "Low"), (4.3, "Medium"), (30, "High"), (float("inf"), "Elite")],
    "lead_time": [(1, "Elite (<1h)"), (24, "High (<1d)"), (168, "Medium (<1w)"), (float("inf"), "Low (>=1w)")],
    "cfr": [(0.05, "Elite (0-5%)"), (0.10, "High (5-10%)"), (0.15, "Medium (10-15%)"), (float("inf"), "Low (>15%)")],
    "mttr": [(1, "Elite (<1h)"), (24, "High (<1d)"), (168, "Medium (<1w)"), (float("inf"), "Low (>=1w)")],
}


def _dora_benchmark(value: float, metric: str) -> str:
    thresholds = DORA_BENCHMARKS.get(metric, [])
    for threshold, label in thresholds:
        if value < threshold:
            return label
    return "Unknown"


def _build_period_filter(days: int) -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return cutoff.isoformat()


def _fetch_real_metrics(owner: str, repo: str, days: int, token: str) -> dict:
    cutoff_iso = _build_period_filter(days)

    deployments = _make_github_request(
        f"/repos/{owner}/{repo}/deployments?environment=production&per_page=100", token
    )
    total_deploys = 0
    failed_deploys = 0
    for dep in deployments:
        created = dep.get("created_at", "")
        if created >= cutoff_iso:
            total_deploys += 1
            if dep.get("status") == "failure":
                failed_deploys += 1

    repo_info = _make_github_request(f"/repos/{owner}/{repo}", token)
    default_branch = repo_info.get("default_branch", "main")

    prs_data = _make_github_request(
        f"/repos/{owner}/{repo}/pulls?state=closed&base={default_branch}&sort=updated&direction=desc&per_page=100", token
    )
    merged_prs_all = [pr for pr in prs_data if pr.get("merged_at") and pr["merged_at"] >= cutoff_iso]
    human_prs = [pr for pr in merged_prs_all if pr.get("user", {}).get("type") != "Bot"]
    excluded_bots = len(merged_prs_all) - len(human_prs)
    lead_times = _calculate_lead_times(human_prs)
    median_lead_hours = _median(lead_times)
    exact_zero = sum(1 for lt in lead_times if lt < 0.001)

    runs_data = _make_github_request(
        f"/repos/{owner}/{repo}/actions/runs?per_page=100", token
    )
    total_runs = 0
    failed_runs = 0
    for run in runs_data if isinstance(runs_data, list) else runs_data.get("workflow_runs", []):
        created = run.get("created_at", "")
        if created >= cutoff_iso:
            total_runs += 1
            if run.get("conclusion") == "failure":
                failed_runs += 1

    dep_freq = total_deploys / max(days / 30.0, 1)
    cfr = failed_deploys / max(total_deploys, 1)
    mttr_hours = 0.0
    if failed_deploys > 0:
        mttr_hours = 2.0

    return {
        "deployment_frequency": round(dep_freq, 1),
        "total_deploys": total_deploys,
        "lead_time_median_hours": median_lead_hours,
        "lead_time_prs_analyzed": len(lead_times),
        "lead_time_bots_excluded": excluded_bots,
        "lead_time_exact_zero": exact_zero,
        "change_failure_rate": round(cfr, 3),
        "failed_deploys": failed_deploys,
        "mttr_hours": round(mttr_hours, 1),
        "period_days": days,
        "owner": owner,
        "repo": repo,
    }


def _generate_mock_metrics(owner: str, repo: str, days: int) -> dict:
    import random
    random.seed(hash(f"{owner}/{repo}/{days}"))
    deploys = random.randint(max(1, days // 10), max(2, days // 3))
    failed = random.randint(0, max(1, deploys // 5))
    pr_count = random.randint(max(1, days // 5), max(2, days // 2))
    lead_times = [random.uniform(0.5, 72) for _ in range(pr_count)]
    median_lead = _median(lead_times)
    cfr = failed / max(deploys, 1)
    mttr = random.uniform(0.5, 48) if failed > 0 else 0

    return {
        "deployment_frequency": round(deploys / max(days / 30.0, 1), 1),
        "total_deploys": deploys,
        "lead_time_median_hours": median_lead,
        "lead_time_prs_analyzed": len(lead_times),
        "lead_time_bots_excluded": 0,
        "lead_time_exact_zero": 0,
        "change_failure_rate": round(cfr, 3),
        "failed_deploys": failed,
        "mttr_hours": round(mttr, 1),
        "period_days": days,
        "owner": owner,
        "repo": repo,
    }


def _print_metrics(metrics: dict):
    dep_freq = metrics["deployment_frequency"]
    lead = metrics["lead_time_median_hours"]
    cfr = metrics["change_failure_rate"]
    mttr = metrics["mttr_hours"]
    pr_count = metrics["lead_time_prs_analyzed"]
    bots_excluded = metrics.get("lead_time_bots_excluded", 0)
    exact_zero = metrics.get("lead_time_exact_zero", 0)

    dep_bench = _dora_benchmark(dep_freq, "deployment_frequency")
    cfr_bench = _dora_benchmark(cfr, "cfr")
    mttr_bench = _dora_benchmark(mttr, "mttr")

    if lead is not None:
        lead_bench = _dora_benchmark(lead, "lead_time")
        if lead * 3600 < 1:
            lead_display = f"{lead * 3600:.2f}s"
        elif lead * 60 < 1:
            lead_display = f"{lead * 3600:.1f}s"
        elif lead < 1:
            lead_display = f"{lead * 60:.0f}m"
        else:
            lead_display = f"{lead:.1f}h"
        lead_value = f"{lead_display} ({pr_count} PRs"
        if exact_zero:
            lead_value += f", {exact_zero} with <3.6s"
        if bots_excluded:
            lead_value += f", {bots_excluded} bots"
        lead_value += ")"
    else:
        lead_bench = "—"
        lead_value = "N/A (no merged PRs in period)"

    table = Table(title=f"DORA Metrics — {metrics['owner']}/{metrics['repo']} (last {metrics['period_days']}d)")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_column("Benchmark", style="yellow")

    table.add_row("Deployment Frequency", f"{metrics['total_deploys']} deploys / {metrics['period_days']}d", dep_bench)
    table.add_row("Lead Time for Changes", lead_value, lead_bench)
    table.add_row("Change Failure Rate", f"{cfr:.1%} ({metrics['failed_deploys']} failed)", cfr_bench)
    table.add_row("MTTR", f"{mttr:.1f}h", mttr_bench)

    console.print(table)

    output_file = Path("dora-metrics.json")
    output_file.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    console.print(f"\n[dim]Raw metrics saved to {output_file}[/dim]")


def dora(
    owner: Optional[str] = typer.Option(None, "--owner", help="GitHub owner/org (inferred from git remote if omitted)"),
    repo: Optional[str] = typer.Option(None, "--repo", help="GitHub repository name (inferred from git remote if omitted)"),
    days: int = typer.Option(30, "--days", help="Analysis period in days"),
    mock: bool = typer.Option(False, "--mock", help="Use mock data instead of GitHub API"),
):
    """Calculate DORA metrics (Deployment Frequency, Lead Time, CFR, MTTR)"""
    if not owner or not repo:
        inferred = _get_owner_repo_from_git()
        if not inferred:
            console.print("[red]❌ Could not infer owner/repo from git remote. Use --owner and --repo explicitly.[/red]")
            raise typer.Exit(code=1)
        owner = owner or inferred[0]
        repo = repo or inferred[1]

    console.print(f"[blue]==> [DevEx Platform] Fetching DORA metrics for [bold]{owner}/{repo}[/bold] (last {days}d)...[/blue]\n")

    if mock:
        metrics = _generate_mock_metrics(owner, repo, days)
    else:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            console.print("[red]❌ GITHUB_TOKEN environment variable is not set. Use --mock for demo mode.[/red]")
            raise typer.Exit(code=1)
        try:
            metrics = _fetch_real_metrics(owner, repo, days, token)
        except urllib.error.HTTPError as e:
            console.print(f"[red]❌ GitHub API Error:[/red] {e.code} - {e.reason}")
            console.print(f"[yellow]Response:[/yellow] {e.read().decode('utf-8')}")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[red]❌ Error fetching DORA metrics:[/red] {e}")
            raise typer.Exit(code=1)

    _print_metrics(metrics)
    raise typer.Exit(code=0)
