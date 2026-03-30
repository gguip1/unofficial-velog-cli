import typer

from postflow.commands.init import init
from postflow.commands.create import create
from postflow.commands.list import list_posts
from postflow.commands.check import check
from postflow.commands.doctor import doctor
from postflow.commands.login import login_cmd
from postflow.commands.publish import publish

app = typer.Typer(
    name="postflow",
    help="Git 기반 마크다운 콘텐츠 퍼블리싱 도구",
    no_args_is_help=True,
)

app.command(name="init")(init)
app.command(name="create")(create)
app.command(name="list")(list_posts)
app.command(name="check")(check)
app.command(name="doctor")(doctor)
app.command(name="login")(login_cmd)
app.command(name="publish")(publish)

if __name__ == "__main__":
    app()
