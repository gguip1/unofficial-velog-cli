from pathlib import Path

from postflow.models import Meta, PostStatus, RegistryEntry, Visibility
from postflow.core.config import load_config
from postflow.core.registry import add_entry
from postflow.utils.fs import read_yaml, write_yaml, read_text, write_text
from postflow.utils.id import generate_id
from postflow.utils.paths import get_post_dir, get_posts_dir


def create_post(
    root: Path,
    title: str,
    slug: str,
    visibility: str = "public",
    series: str | None = None,
) -> Meta:
    config = load_config(root)
    posts_dir = get_posts_dir(root, config.posts_dir)
    post_dir = posts_dir / slug

    if post_dir.exists():
        raise FileExistsError(f"이미 같은 슬러그의 디렉토리가 존재합니다: {slug}")

    post_id = generate_id()

    meta = Meta(
        id=post_id,
        title=title,
        slug=slug,
        description="",
        tags=[],
        status=PostStatus(config.settings.default_status),
        visibility=Visibility(visibility),
        series=series,
    )

    # 디렉토리 및 파일 생성
    post_dir.mkdir(parents=True)
    write_yaml(post_dir / "meta.yaml", meta.model_dump(mode="json"))

    template_path = root / "templates" / "content.md"
    if template_path.exists():
        content = read_text(template_path).replace("# 제목", f"# {title}")
    else:
        content = f"# {title}\n\n여기에 글을 작성하세요.\n"
    write_text(post_dir / "content.md", content)

    # 레지스트리에 등록
    entry = RegistryEntry(
        id=post_id,
        slug=slug,
        directory=f"{config.posts_dir}/{slug}",
        title=title,
        status=meta.status,
        visibility=meta.visibility,
        series=series,
        provider=None,
        last_published_at=None,
    )
    add_entry(root, entry)

    return meta


def read_post(root: Path, slug: str) -> tuple[Meta, str]:
    config = load_config(root)
    post_dir = get_post_dir(root, slug, config.posts_dir)

    if not post_dir.exists():
        raise FileNotFoundError(f"글 디렉토리를 찾을 수 없습니다: {slug}")

    meta_data = read_yaml(post_dir / "meta.yaml")
    meta = Meta(**meta_data)

    content = read_text(post_dir / "content.md")

    return meta, content
