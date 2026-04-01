from pathlib import Path

from vcli.models import Config
from vcli.utils.fs import read_yaml, write_yaml
from vcli.utils.paths import get_config_path


def load_config(root: Path) -> Config:
    path = get_config_path(root)
    if not path.exists():
        raise FileNotFoundError(
            f"설정 파일을 찾을 수 없습니다: {path}\n"
            "'vcli init'을 먼저 실행하세요."
        )
    data = read_yaml(path)
    return Config(**data)


def save_config(root: Path, config: Config) -> None:
    path = get_config_path(root)
    write_yaml(path, config.model_dump())


def config_exists(root: Path) -> bool:
    return get_config_path(root).exists()
