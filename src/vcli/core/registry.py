from pathlib import Path

from vcli.models import Registry, RegistryEntry
from vcli.utils.fs import read_yaml, write_yaml
from vcli.utils.paths import get_registry_path


def load_registry(root: Path) -> Registry:
    path = get_registry_path(root)
    if not path.exists():
        return Registry()
    data = read_yaml(path)
    return Registry(**data)


def save_registry(root: Path, registry: Registry) -> None:
    path = get_registry_path(root)
    write_yaml(path, registry.model_dump(mode="json"))


def add_entry(root: Path, entry: RegistryEntry) -> None:
    registry = load_registry(root)

    for existing in registry.posts:
        if existing.id == entry.id:
            raise ValueError(f"이미 같은 ID의 글이 존재합니다: {entry.id}")
        if existing.slug == entry.slug:
            raise ValueError(f"이미 같은 슬러그의 글이 존재합니다: {entry.slug}")

    registry.posts.append(entry)
    save_registry(root, registry)


def find_entry(root: Path, id_or_slug: str) -> RegistryEntry | None:
    registry = load_registry(root)
    for entry in registry.posts:
        if entry.id == id_or_slug or entry.slug == id_or_slug:
            return entry
        if entry.id.startswith(id_or_slug):
            return entry
    return None


def update_entry(root: Path, entry_id: str, **updates) -> None:
    registry = load_registry(root)
    for i, entry in enumerate(registry.posts):
        if entry.id == entry_id:
            updated = entry.model_copy(update=updates)
            registry.posts[i] = updated
            save_registry(root, registry)
            return
    raise ValueError(f"해당 ID의 글을 찾을 수 없습니다: {entry_id}")
