from pathlib import Path

import typer

from postflow.core.config import config_exists, save_config
from postflow.models import Config
from postflow.utils import logger
from postflow.utils.fs import write_yaml
from postflow.utils.paths import get_posts_dir, get_registry_path


def init(
    path: Path = typer.Option(
        ".", "--path", "-p", help="프로젝트 경로 (기본: 현재 디렉토리)"
    ),
) -> None:
    """PostFlow 프로젝트를 초기화합니다."""
    root = path.resolve()

    if config_exists(root):
        logger.warn("이미 초기화된 프로젝트입니다.")
        overwrite = typer.confirm("설정을 다시 생성할까요?", default=False)
        if not overwrite:
            raise typer.Exit()

    # Velog username 입력
    username = typer.prompt("Velog 사용자명을 입력하세요")

    config = Config()
    config.velog.username = username
    save_config(root, config)
    logger.success(f"설정 파일 생성: postflow.config.yaml")

    # posts 디렉토리 확인
    posts_dir = get_posts_dir(root, config.posts_dir)
    if not posts_dir.exists():
        posts_dir.mkdir(parents=True)
        logger.success(f"글 디렉토리 생성: {config.posts_dir}/")
    else:
        logger.info(f"글 디렉토리 확인: {config.posts_dir}/")

    # posts/registry.yaml 확인
    registry_path = get_registry_path(root, config.posts_dir)
    if not registry_path.exists():
        write_yaml(registry_path, {"posts": []})
        logger.success("레지스트리 생성: posts/registry.yaml")
    else:
        logger.info("레지스트리 확인: posts/registry.yaml")

    logger.success("PostFlow 초기화 완료!")
    logger.info("'postflow create'로 첫 번째 글을 만들어보세요.")
