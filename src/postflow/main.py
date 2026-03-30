import typer

from postflow.commands.init import init
from postflow.commands.create import create

app = typer.Typer(
    name="postflow",
    help="Git 기반 마크다운 콘텐츠 퍼블리싱 도구",
    no_args_is_help=True,
)

app.command(name="init")(init)
app.command(name="create")(create)

if __name__ == "__main__":
    app()
