import typer

from devex_cli.commands.check_branch import check_branch
from devex_cli.commands.init import init
from devex_cli.commands.pr import pr_create
from devex_cli.commands.validate import validate
from devex_cli.commands.dora import dora

app = typer.Typer(help="DevEx Golden Path CLI")

app.command(name="check-branch")(check_branch)
app.command(name="init")(init)
app.command(name="pr-create")(pr_create)
app.command(name="validate")(validate)
app.command(name="dora")(dora)

if __name__ == "__main__":
    app()