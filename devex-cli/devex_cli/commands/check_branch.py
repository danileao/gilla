import typer
import re
from rich.console import Console
from pathlib import Path
from devex_cli.constants import WORK_ID_REGEX

try:
    from git import Repo
except ImportError:
    Repo = None


console = Console()



def check_branch():
    """Valida automaticamente se a branch atual segue a convenção..."""
    if not Path(".git").exists():
        console.print("[red]Erro: [/red] This commands needs to be used inside git repository")
        raise typer.Exit(code=0)

    if Repo is None:
        console.print("[red]❌ Erro:[/red] A biblioteca 'gitpython' não está instalada corretamente.")
        raise typer.Exit(code=1)
        
    try:
        repo = Repo(".")
        if repo.head.is_detached:
            console.print("[yellow]⚠ HEAD em estado detached (sem branch ativa). Pulando validação de Work ID.[/yellow]")
            raise typer.Exit(code=0)

        branch_name = repo.active_branch.name

        if branch_name in ["main", "master", "development", "dev"]:
            console.print(f"[yellow]⚠ Ignorando validação:[/yellow] Você está na branch principal '{branch_name}'.")
            raise typer.Exit(code=0)
        
        if re.match(WORK_ID_REGEX, branch_name):
            console.print(f"[green]✔ Branch atual '{branch_name}' válida para o Work ID![/green]")
            raise typer.Exit(code=0)
        else:
            console.print(f"[red]❌ Erro de Governança:[/red] A sua branch atual '[bold]{branch_name}[/bold]' não segue o padrão do Work ID.")
            console.print("[yellow]💡 Padrão exigido:[/yellow] FIN-Número-sua-feature (Ex: [green]FIN-123-ajuste-token[/green])")
            raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]❌ Erro ao ler informações do Git:[/red] {str(e)}")
        raise typer.Exit(code=1)
