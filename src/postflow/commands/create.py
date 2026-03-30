import re
from pathlib import Path

import typer

from postflow.core.post import create_post
from postflow.utils import logger
from postflow.utils.paths import find_project_root


def _slugify(text: str) -> str:
    """제목을 슬러그로 변환한다."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text


def create(
    title: str = typer.Option(None, "--title", "-t", help="글 제목"),
    slug: str = typer.Option(None, "--slug", "-s", help="URL 슬러그"),
    visibility: str = typer.Option("public", "--visibility", "-v", help="공개 여부 (public/private)"),
    series: str = typer.Option(None, "--series", help="Velog 시리즈명"),
) -> None:
    """새 글을 생성합니다."""
    root = find_project_root()

    # 대화형 입력
    if title is None:
        title = typer.prompt("글 제목")

    if slug is None:
        suggested = _slugify(title)
        slug = typer.prompt("슬러그 (URL용)", default=suggested)

    try:
        meta = create_post(
            root=root,
            title=title,
            slug=slug,
            visibility=visibility,
            series=series,
        )
        logger.success(f"글 생성 완료: posts/{slug}/")
        logger.info(f"  ID: {meta.id}")
        logger.info(f"  제목: {meta.title}")
        logger.info(f"  상태: {meta.status.value}")
        logger.info(f"posts/{slug}/content.md 를 편집해서 글을 작성하세요.")
    except FileExistsError as e:
        logger.error(str(e))
        raise typer.Exit(1)
    except ValueError as e:
        logger.error(str(e))
        raise typer.Exit(1)
