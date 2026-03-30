import typer
from rich.table import Table

from postflow.core.registry import load_registry
from postflow.utils.logger import console
from postflow.utils.paths import find_project_root


def list_posts(
    status: str = typer.Option(None, "--status", "-s", help="상태 필터 (draft/ready/published)"),
) -> None:
    """글 목록을 출력합니다."""
    root = find_project_root()
    registry = load_registry(root)

    posts = registry.posts
    if status:
        posts = [p for p in posts if p.status.value == status]

    if not posts:
        if status:
            console.print(f"상태가 '{status}'인 글이 없습니다.")
        else:
            console.print("등록된 글이 없습니다. 'postflow create'로 글을 만들어보세요.")
        return

    table = Table(title=f"글 목록 (총 {len(posts)}개)")
    table.add_column("슬러그", style="cyan")
    table.add_column("제목")
    table.add_column("상태", style="green")
    table.add_column("공개", style="yellow")
    table.add_column("시리즈", style="dim")

    for post in posts:
        table.add_row(
            post.slug,
            post.title,
            post.status.value,
            post.visibility.value,
            post.series or "",
        )

    console.print(table)
