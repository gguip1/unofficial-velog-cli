from pathlib import Path

CONFIG_FILENAME = "postflow.config.yaml"
REGISTRY_FILENAME = "registry.yaml"


def find_project_root(start: Path | None = None) -> Path:
    """postflow.config.yaml 또는 registry.yaml이 있는 디렉토리를 찾는다."""
    current = start or Path.cwd()

    for parent in [current, *current.parents]:
        if (parent / CONFIG_FILENAME).exists() or (parent / REGISTRY_FILENAME).exists():
            return parent

    return current


def get_posts_dir(root: Path, posts_dir_name: str = "posts") -> Path:
    return root / posts_dir_name


def get_post_dir(root: Path, slug: str, posts_dir_name: str = "posts") -> Path:
    return root / posts_dir_name / slug


def get_registry_path(root: Path) -> Path:
    return root / REGISTRY_FILENAME


def get_config_path(root: Path) -> Path:
    return root / CONFIG_FILENAME
