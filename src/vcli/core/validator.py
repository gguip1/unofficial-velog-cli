from pathlib import Path

from pydantic import ValidationError

from vcli.core.config import load_config
from vcli.core.registry import load_registry
from vcli.models import Meta
from vcli.utils.fs import read_yaml
from vcli.utils.paths import get_posts_dir


class CheckResult:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def merge(self, other: "CheckResult") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def validate_post(root: Path, slug: str) -> CheckResult:
    """단일 글의 메타데이터와 파일 구조를 검증한다."""
    result = CheckResult()
    config = load_config(root)
    post_dir = get_posts_dir(root, config.posts_dir) / slug

    # 디렉토리 존재 확인
    if not post_dir.exists():
        result.add_error(f"[{slug}] 글 디렉토리가 존재하지 않습니다")
        return result

    # content.md 존재 확인
    content_path = post_dir / "content.md"
    if not content_path.exists():
        result.add_error(f"[{slug}] content.md 파일이 없습니다")

    # meta.yaml 존재 및 스키마 검증
    meta_path = post_dir / "meta.yaml"
    if not meta_path.exists():
        result.add_error(f"[{slug}] meta.yaml 파일이 없습니다")
        return result

    try:
        data = read_yaml(meta_path)
        meta = Meta(**data)
    except ValidationError as e:
        for err in e.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            result.add_error(f"[{slug}] meta.yaml 검증 실패 - {field}: {err['msg']}")
        return result

    # slug 일치 확인
    if meta.slug != slug:
        result.add_error(
            f"[{slug}] meta.yaml의 slug({meta.slug})가 디렉토리명({slug})과 다릅니다"
        )

    # 필수 필드 확인
    if not meta.id:
        result.add_error(f"[{slug}] meta.yaml에 id가 비어있습니다")
    if not meta.title:
        result.add_error(f"[{slug}] meta.yaml에 title이 비어있습니다")

    return result


def validate_registry(root: Path) -> CheckResult:
    """레지스트리와 파일 시스템의 정합성을 검증한다."""
    result = CheckResult()
    config = load_config(root)
    registry = load_registry(root)
    posts_dir = get_posts_dir(root, config.posts_dir)

    seen_ids: set[str] = set()
    seen_slugs: set[str] = set()

    for entry in registry.posts:
        # id 중복
        if entry.id in seen_ids:
            result.add_error(f"레지스트리에 중복 ID가 있습니다: {entry.id}")
        seen_ids.add(entry.id)

        # slug 중복
        if entry.slug in seen_slugs:
            result.add_error(f"레지스트리에 중복 슬러그가 있습니다: {entry.slug}")
        seen_slugs.add(entry.slug)

        # 디렉토리 존재 확인
        post_dir = posts_dir / entry.slug
        if not post_dir.exists():
            result.add_error(
                f"[{entry.slug}] 레지스트리에 있지만 디렉토리가 없습니다"
            )

    # 파일 시스템에 있지만 레지스트리에 없는 글 찾기
    if posts_dir.exists():
        for child in posts_dir.iterdir():
            if child.is_dir() and (child / "meta.yaml").exists():
                if child.name not in seen_slugs:
                    result.add_warning(
                        f"[{child.name}] 디렉토리에 있지만 레지스트리에 등록되지 않았습니다"
                    )

    return result


def validate_all(root: Path) -> CheckResult:
    """전체 프로젝트를 검증한다."""
    result = CheckResult()
    config = load_config(root)
    posts_dir = get_posts_dir(root, config.posts_dir)

    # 레지스트리 검증
    registry_result = validate_registry(root)
    result.merge(registry_result)

    # 각 글 검증
    if posts_dir.exists():
        for child in sorted(posts_dir.iterdir()):
            if child.is_dir() and (child / "meta.yaml").exists():
                post_result = validate_post(root, child.name)
                result.merge(post_result)

    return result
