import asyncio
from datetime import datetime, timezone
from typing import Optional

import typer
from InquirerPy import inquirer

from postflow.adapters.velog.adapter import VelogAdapter
from postflow.adapters.velog.auth import check_auth
from postflow.adapters.velog.mapper import to_post_data
from postflow.core.post import read_post
from postflow.core.registry import find_entry, load_registry, update_entry
from postflow.core.validator import validate_post
from postflow.models import PostStatus, ProviderInfo, RegistryEntry
from postflow.utils import logger
from postflow.utils.paths import find_project_root


def _process_images(content: str, post_dir) -> str:
    """로컬 이미지를 처리한다.
    - mapping.json에 있는 이미지: 원본 URL로 복원
    - mapping.json에 없는 로컬 이미지: Velog에 업로드 후 URL 치환
    """
    import re
    import json
    from pathlib import Path
    from postflow.adapters.velog.api import upload_image

    post_dir = Path(post_dir)
    images_dir = post_dir / "images"

    # 기존 매핑 로드
    mapping_path = images_dir / "mapping.json"
    if mapping_path.exists():
        with open(mapping_path, encoding="utf-8") as f:
            mapping = json.load(f)
    else:
        mapping = {}

    # mapping에 있는 이미지는 원본 URL로 복원
    for local_ref, original_url in mapping.items():
        content = content.replace(local_ref, original_url)

    # 아직 로컬 경로로 남아있는 이미지 찾기 (새로 추가된 이미지)
    local_refs = re.findall(r'!\[[^\]]*\]\((\.\/images\/[^)]+)\)', content)

    for local_ref in local_refs:
        image_path = post_dir / local_ref.lstrip("./")
        if not image_path.exists():
            continue

        try:
            logger.info(f"    이미지 업로드: {image_path.name}")
            url = upload_image(image_path)
            content = content.replace(local_ref, url)
            # 매핑에 추가
            mapping[local_ref] = url
        except Exception as e:
            logger.warn(f"    이미지 업로드 실패: {image_path.name} ({e})")

    # 매핑 저장
    if mapping:
        images_dir.mkdir(exist_ok=True)
        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2)

    return content


def _publish_entry(root, entry: RegistryEntry, adapter: VelogAdapter) -> bool:
    """단일 글을 발행한다. 성공 시 True 반환."""
    # 검증
    check_result = validate_post(root, entry.slug)
    if not check_result.ok:
        for err in check_result.errors:
            logger.error(err)
        return False

    # 글 읽기
    meta, content = read_post(root, entry.slug)

    # 로컬 이미지 경로를 원본 URL로 되돌리기
    from postflow.core.config import load_config
    from postflow.utils.paths import get_posts_dir
    config = load_config(root)
    post_dir = get_posts_dir(root, config.posts_dir) / entry.slug
    content = _process_images(content, post_dir)

    post_data = to_post_data(meta, content)

    # 신규 vs 수정 판단
    if entry.provider and entry.provider.post_id:
        logger.info(f"  수정: {meta.title}")
        result = asyncio.run(adapter.update(entry.provider.post_id, post_data))
    else:
        logger.info(f"  발행: {meta.title}")
        result = asyncio.run(adapter.create(post_data))

    if result.success:
        logger.success(f"  완료: {result.url}")
        update_entry(
            root,
            entry.id,
            status=PostStatus.published,
            provider=ProviderInfo(
                name="velog",
                post_id=result.post_id,
                url=result.url,
            ),
            last_published_at=datetime.now(timezone.utc),
        )
        return True
    else:
        logger.error(f"  실패: {result.error}")
        return False


def publish(
    id_or_slug: Optional[str] = typer.Option(None, "--slug", "-s", help="글 ID 또는 슬러그 (생략 시 선택)"),
) -> None:
    """글을 Velog에 발행합니다."""
    root = find_project_root()

    # 인증 확인
    if not check_auth():
        logger.error("Velog에 로그인되어 있지 않습니다. 'postflow login'을 먼저 실행하세요.")
        raise typer.Exit(1)

    adapter = VelogAdapter()

    # 인자가 있으면 바로 발행
    if id_or_slug:
        entry = find_entry(root, id_or_slug)
        if not entry:
            logger.error(f"'{id_or_slug}'에 해당하는 글을 찾을 수 없습니다.")
            raise typer.Exit(1)
        if not _publish_entry(root, entry, adapter):
            raise typer.Exit(1)
        return

    # 인자 없으면 발행할 글 선택
    registry = load_registry(root)
    if not registry.posts:
        logger.info("등록된 글이 없습니다.")
        raise typer.Exit()

    # 변경된 글만 필터링
    from postflow.utils.fs import read_yaml
    from postflow.utils.paths import get_posts_dir
    from postflow.core.config import load_config
    from datetime import datetime

    config = load_config(root)
    posts_dir = get_posts_dir(root, config.posts_dir)

    choices = []
    for entry in registry.posts:
        # 신규 글 (아직 발행 안 됨)
        if not entry.provider or not entry.provider.post_id:
            label = f"[신규] {entry.title} ({entry.slug})"
            choices.append({"name": label, "value": entry.slug})
            continue

        # 기존 글: 파일 수정 시간 vs 마지막 발행 시간 비교
        post_dir = posts_dir / entry.slug
        content_path = post_dir / "content.md"
        meta_path = post_dir / "meta.yaml"
        if not content_path.exists():
            continue

        last_published = entry.last_published_at
        if last_published:
            last_pub_ts = last_published.timestamp()
            content_mtime = content_path.stat().st_mtime
            meta_mtime = meta_path.stat().st_mtime if meta_path.exists() else 0
            latest_mtime = max(content_mtime, meta_mtime)
            if latest_mtime <= last_pub_ts:
                continue

        label = f"[수정] {entry.title} ({entry.slug})"
        choices.append({"name": label, "value": entry.slug})

    if not choices:
        logger.info("발행할 변경사항이 없습니다.")
        raise typer.Exit()

    selected = inquirer.checkbox(
        message="발행할 글을 선택하세요 (Space로 선택, Enter로 확인)",
        choices=choices,
        enabled_symbol="[x]",
        disabled_symbol="[ ]",
    ).execute()

    if not selected:
        logger.info("선택된 글이 없습니다.")
        return

    success_count = 0
    fail_count = 0

    for slug in selected:
        entry = find_entry(root, slug)
        if entry and _publish_entry(root, entry, adapter):
            success_count += 1
        else:
            fail_count += 1

    logger.info("")
    logger.success(f"완료! {success_count}개 발행, {fail_count}개 실패")
