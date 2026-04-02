import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlparse, unquote
import hashlib

import typer

from vcli.adapters.velog.api import get_current_user, get_user_posts
from vcli.adapters.velog.auth import check_auth
from vcli.core.config import load_config
from vcli.core.registry import add_entry, load_registry, update_entry
from vcli.models import Meta, PostStatus, ProviderInfo, RegistryEntry, Visibility
from vcli.utils import logger
from vcli.utils.fs import read_yaml, write_yaml, write_text
from vcli.utils.id import generate_id
from vcli.utils.paths import find_project_root, get_posts_dir


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def _find_image_urls(body: str) -> list[str]:
    """본문에서 모든 이미지 URL을 찾는다. 마크다운과 HTML 태그 모두 지원."""
    urls = []
    # 마크다운: ![alt](url)
    for match in re.finditer(r"!\[[^\]]*\]\((https?://[^)]+)\)", body):
        urls.append(match.group(1))
    # HTML: <img src="url">
    for match in re.finditer(r'<img[^>]+src=["\']?(https?://[^"\'>\s]+)', body):
        urls.append(match.group(1))
    return urls


def _make_filename(url: str, index: int) -> str:
    """URL에서 안전한 파일명을 생성한다."""
    parsed = urlparse(url)
    original = unquote(parsed.path.split("/")[-1])

    # 확장자 추출
    ext = ".png"
    if "." in original:
        ext = "." + original.rsplit(".", 1)[-1].lower()
        if len(ext) > 5:
            ext = ".png"

    # 짧고 안전한 파일명 생성
    name_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"image-{index + 1}-{name_hash}{ext}"


def _download_images(body: str, post_dir: Path) -> str:
    """본문에서 이미지 URL을 찾아 다운로드하고, 경로를 로컬로 치환한다.
    원본 URL 매핑을 images/mapping.json에 저장한다."""
    urls = _find_image_urls(body)

    if not urls:
        return body

    images_dir = post_dir / "images"
    images_dir.mkdir(exist_ok=True)

    # 기존 매핑 로드
    mapping_path = images_dir / "mapping.json"
    import json
    if mapping_path.exists():
        with open(mapping_path, encoding="utf-8") as f:
            mapping = json.load(f)
    else:
        mapping = {}

    downloaded = 0
    for i, url in enumerate(urls):
        try:
            filename = _make_filename(url, i)
            local_path = images_dir / filename

            if not local_path.exists():
                req = Request(url, headers={"User-Agent": "unofficial-velog-cli/0.1"})
                with urlopen(req, timeout=30) as resp:
                    local_path.write_bytes(resp.read())

            local_ref = f"./images/{filename}"
            mapping[local_ref] = url
            body = body.replace(url, local_ref)
            downloaded += 1
        except Exception:
            pass

    # 매핑 저장
    if mapping:
        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2)

    if downloaded > 0:
        logger.info(f"    이미지 {downloaded}/{len(urls)}개 다운로드")

    return body


def sync_posts() -> None:
    """Velog의 글을 로컬과 동기화합니다. 새 글은 가져오고, 변경된 글은 업데이트합니다."""
    root = find_project_root()

    if not check_auth():
        logger.error("Velog에 로그인되어 있지 않습니다. 'vcli login'을 먼저 실행하세요.")
        raise typer.Exit(1)

    user = get_current_user()
    if not user:
        logger.error("사용자 정보를 가져올 수 없습니다.")
        raise typer.Exit(1)

    username = user["username"]
    logger.info(f"Velog 사용자: {username}")
    logger.info("글 목록을 가져오는 중...")

    posts = get_user_posts(username)
    if not posts:
        logger.info("동기화할 글이 없습니다.")
        return

    logger.info(f"총 {len(posts)}개 글을 발견했습니다.")

    config = load_config(root)
    registry = load_registry(root)
    posts_dir = get_posts_dir(root, config.posts_dir)

    # velog post_id → registry entry 매핑
    velog_id_to_entry = {}
    for entry in registry.posts:
        if entry.provider and entry.provider.post_id:
            velog_id_to_entry[entry.provider.post_id] = entry

    created = 0
    updated = 0
    skipped = 0

    for post in posts:
        slug = post["url_slug"] or _slugify(post["title"])
        title = post["title"]
        velog_post_id = post["id"]

        # 이미 동기화된 글인지 확인 (velog post_id로 매칭)
        existing_entry = velog_id_to_entry.get(velog_post_id)

        if existing_entry:
            post_dir = posts_dir / existing_entry.slug

            # Velog 수정 일자 확인
            released = post.get("released_at")
            if released:
                velog_updated = datetime.fromisoformat(released.replace("Z", "+00:00"))
            else:
                velog_updated = datetime.now(timezone.utc)

            # 로컬 파일 수정 시간 vs Velog 수정 시간 비교
            content_path = post_dir / "content.md"
            if content_path.exists():
                local_mtime = datetime.fromtimestamp(content_path.stat().st_mtime, tz=timezone.utc)
                if local_mtime > velog_updated:
                    logger.warn(f"  로컬이 더 최신입니다: {title}")
                    logger.info(f"    Velog에 반영하려면 'vcli publish --slug {existing_entry.slug}'를 사용하세요.")
                    overwrite = typer.confirm(f"  Velog 내용으로 로컬을 덮어쓸까요?", default=False)
                    if not overwrite:
                        skipped += 1
                        continue

            # 기존 글 업데이트
            if not post_dir.exists():
                post_dir.mkdir(parents=True)

            body = post.get("body", "") or ""
            body = _download_images(body, post_dir)
            write_text(post_dir / "content.md", body)

            series_name = None
            if post.get("series"):
                series_name = post["series"]["name"]

            meta_data = {
                "id": existing_entry.id,
                "title": title,
                "slug": existing_entry.slug,
                "description": post.get("short_description", "") or "",
                "tags": post.get("tags", []),
                "status": PostStatus.published.value,
                "visibility": Visibility.private.value if post.get("is_private") else Visibility.public.value,
                "series": series_name,
            }
            write_yaml(post_dir / "meta.yaml", meta_data)

            # 레지스트리 업데이트
            update_entry(
                root,
                existing_entry.id,
                title=title,
                visibility=Visibility.private if post.get("is_private") else Visibility.public,
                series=series_name,
            )

            logger.info(f"  업데이트: {title}")
            updated += 1
        else:
            # 새 글 가져오기
            post_dir = posts_dir / slug
            post_id = generate_id()
            released = post.get("released_at")
            published_at = None
            if released:
                published_at = datetime.fromisoformat(released.replace("Z", "+00:00"))

            series_name = None
            if post.get("series"):
                series_name = post["series"]["name"]

            meta = Meta(
                id=post_id,
                title=title,
                slug=slug,
                description=post.get("short_description", "") or "",
                tags=post.get("tags", []),
                status=PostStatus.published,
                visibility=Visibility.private if post.get("is_private") else Visibility.public,
                series=series_name,
            )

            if not post_dir.exists():
                post_dir.mkdir(parents=True)

            body = post.get("body", "") or ""
            body = _download_images(body, post_dir)

            write_yaml(post_dir / "meta.yaml", meta.model_dump(mode="json"))
            write_text(post_dir / "content.md", body)

            entry = RegistryEntry(
                id=post_id,
                slug=slug,
                directory=f"{config.posts_dir}/{slug}",
                title=title,
                status=meta.status,
                visibility=meta.visibility,
                series=series_name,
                provider=ProviderInfo(
                    name="velog",
                    post_id=velog_post_id,
                    url=f"https://velog.io/@{username}/{slug}",
                ),
                last_published_at=published_at,
            )
            add_entry(root, entry)

            logger.success(f"  가져옴: {title}")
            created += 1

    # Velog에서 삭제된 글 감지
    velog_post_ids = {p["id"] for p in posts}
    deleted = 0
    entries_to_remove = []

    for entry in registry.posts:
        if entry.provider and entry.provider.post_id:
            if entry.provider.post_id not in velog_post_ids:
                logger.warn(f"  Velog에서 삭제됨: {entry.title}")
                remove = typer.confirm(f"  로컬에서도 삭제할까요?", default=False)
                if remove:
                    post_dir = posts_dir / entry.slug
                    if post_dir.exists():
                        import shutil
                        shutil.rmtree(post_dir)
                    entries_to_remove.append(entry.id)
                    deleted += 1

    # 레지스트리에서 삭제된 항목 제거
    if entries_to_remove:
        registry = load_registry(root)
        registry.posts = [e for e in registry.posts if e.id not in entries_to_remove]
        from vcli.core.registry import save_registry
        save_registry(root, registry)

    logger.info("")
    logger.success(f"완료! {created}개 가져옴, {updated}개 업데이트, {skipped}개 건너뜀, {deleted}개 삭제")
