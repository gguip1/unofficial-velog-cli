import typer

from vcli.core.validator import validate_all, validate_post
from vcli.utils import logger
from vcli.utils.paths import find_project_root


def check(
    slug: str = typer.Argument(None, help="검증할 글의 슬러그 (생략 시 전체 검증)"),
) -> None:
    """메타데이터와 파일 구조를 검증합니다."""
    root = find_project_root()

    try:
        if slug:
            result = validate_post(root, slug)
        else:
            result = validate_all(root)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise typer.Exit(1)

    for warning in result.warnings:
        logger.warn(warning)

    for error in result.errors:
        logger.error(error)

    if result.ok:
        if slug:
            logger.success(f"[{slug}] 검증 통과")
        else:
            logger.success("전체 검증 통과")
    else:
        error_count = len(result.errors)
        logger.error(f"검증 실패: {error_count}개 오류 발견")
        raise typer.Exit(1)
