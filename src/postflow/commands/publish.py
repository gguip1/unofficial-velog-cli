import asyncio
from datetime import datetime, timezone

import typer

from postflow.adapters.velog.adapter import VelogAdapter
from postflow.adapters.velog.mapper import to_post_data
from postflow.core.post import read_post
from postflow.core.registry import find_entry, load_registry, update_entry
from postflow.core.validator import validate_post
from postflow.models import ProviderInfo
from postflow.utils import logger
from postflow.utils.paths import find_project_root


def publish(
    id_or_slug: str = typer.Argument(..., help="글 ID 또는 슬러그"),
) -> None:
    """글을 Velog에 발행합니다."""
    root = find_project_root()

    # 글 찾기
    entry = find_entry(root, id_or_slug)
    if not entry:
        logger.error(f"'{id_or_slug}'에 해당하는 글을 찾을 수 없습니다.")
        raise typer.Exit(1)

    # 검증
    check_result = validate_post(root, entry.slug)
    if not check_result.ok:
        for err in check_result.errors:
            logger.error(err)
        logger.error("검증 실패. 발행을 중단합니다.")
        raise typer.Exit(1)

    # 글 읽기
    meta, content = read_post(root, entry.slug)

    # 인증 확인
    from postflow.adapters.velog.auth import check_auth
    adapter = VelogAdapter()
    if not check_auth():
        logger.error("Velog에 로그인되어 있지 않습니다. 'postflow login'을 먼저 실행하세요.")
        raise typer.Exit(1)

    # 발행 데이터 준비
    post_data = to_post_data(meta, content)

    # 신규 vs 수정 판단
    if entry.provider and entry.provider.url:
        logger.info(f"기존 글 수정: {entry.provider.url}")
        result = asyncio.run(adapter.update(entry.provider.url, post_data))
    else:
        logger.info(f"새 글 발행: {meta.title}")
        result = asyncio.run(adapter.create(post_data))

    if result.success:
        logger.success(f"발행 완료: {result.url}")

        # 레지스트리 업데이트
        update_entry(
            root,
            entry.id,
            status="published",
            provider=ProviderInfo(
                name="velog",
                post_id=result.post_id,
                url=result.url,
            ),
            last_published_at=datetime.now(timezone.utc),
        )
        logger.info("레지스트리 업데이트 완료")
    else:
        logger.error(f"발행 실패: {result.error}")
        raise typer.Exit(1)
