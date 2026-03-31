import shutil
import sys

import typer

from postflow.core.config import config_exists, load_config
from postflow.utils import logger
from postflow.utils.paths import find_project_root, get_posts_dir, get_registry_path


def doctor() -> None:
    """환경과 설정 상태를 점검합니다."""
    root = find_project_root()
    all_ok = True

    # Python 버전
    ver = sys.version_info
    if ver >= (3, 12):
        logger.success(f"Python {ver.major}.{ver.minor}.{ver.micro}")
    else:
        logger.error(f"Python {ver.major}.{ver.minor}.{ver.micro} (3.12 이상 필요)")
        all_ok = False

    # config/postflow.yaml
    if config_exists(root):
        config = load_config(root)
        if config.velog.username:
            logger.success(f"설정 파일: config/postflow.yaml (velog: {config.velog.username})")
        else:
            logger.warn("설정 파일: config/postflow.yaml (velog username이 비어있음)")
            all_ok = False
    else:
        logger.error("설정 파일 없음 - 'postflow init'을 실행하세요")
        all_ok = False

    # posts/registry.yaml
    registry_path = get_registry_path(root)
    if registry_path.exists():
        logger.success("레지스트리: posts/registry.yaml")
    else:
        logger.error("레지스트리 없음 - 'postflow init'을 실행하세요")
        all_ok = False

    # posts 디렉토리
    posts_dir = get_posts_dir(root)
    if posts_dir.exists():
        post_count = sum(
            1 for d in posts_dir.iterdir()
            if d.is_dir() and (d / "meta.yaml").exists()
        )
        logger.success(f"글 디렉토리: posts/ ({post_count}개 글)")
    else:
        logger.error("글 디렉토리 없음 - 'postflow init'을 실행하세요")
        all_ok = False

    # Velog 인증 상태
    from postflow.adapters.velog.auth import check_auth, auth_exists
    if auth_exists():
        if check_auth():
            logger.success("Velog 인증: 유효")
        else:
            logger.warn("Velog 인증: 토큰 만료 - 'postflow login'을 실행하세요")
    else:
        logger.info("Velog 인증: 미로그인 - 'postflow login'을 실행하세요")

    # gh CLI
    if shutil.which("gh"):
        logger.success("GitHub CLI: 설치됨")
    else:
        logger.info("GitHub CLI: 미설치 (선택사항)")

    # 결과
    if all_ok:
        logger.success("모든 점검 통과!")
    else:
        logger.warn("일부 항목에 문제가 있습니다. 위 내용을 확인하세요.")
