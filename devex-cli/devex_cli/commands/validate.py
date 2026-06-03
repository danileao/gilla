import json
import subprocess
import typer
from pathlib import Path
from rich.console import Console

console = Console()


def _load_build_steps() -> list[str]:
    config_path = Path("devex.json")
    if not config_path.exists():
        return []
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        return config.get("buildSteps", [])
    except (json.JSONDecodeError, Exception):
        return []


def _run_validation() -> bool:
    """Run build steps and return True if all pass, False otherwise."""
    steps = _load_build_steps()
    if not steps:
        console.print("[yellow]⚠ No build steps found in devex.json.[/yellow]")
        return True

    console.print("[blue]==> [DevEx Platform] Running Shift-Left validations...[/blue]")

    for i, step in enumerate(steps, 1):
        console.print(f"  [{i}/{len(steps)}] Running: [bold]{step}[/bold]")
        result = subprocess.run(step, shell=True, capture_output=True, text=True)

        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                console.print(f"    {line}")

        if result.returncode != 0:
            if result.stderr:
                for line in result.stderr.strip().split("\n"):
                    console.print(f"    [red]{line}[/red]")
            console.print(f"  [red]✖ Step failed (exit code {result.returncode})[/red]")
            console.print("[red]❌ [DevEx Platform] Shift-Left validation FAILED.[/red]")
            return False

        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                console.print(f"    [yellow]{line}[/yellow]")

    console.print("[green]✔ [DevEx Platform] All Shift-Left validations passed![/green]")
    return True


def validate():
    """Run all build steps defined in devex.json (test, lint, etc.)"""
    if not _run_validation():
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)
