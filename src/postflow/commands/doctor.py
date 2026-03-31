import shutil
import subprocess
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

    # Playwright
    try:
        result = subprocess.run(
            [sys.executable, "-c", "from playwright.sync_api import sync_playwright"],
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            logger.success("Playwright: 설치됨")
        else:
            logger.warn("Playwright: 모듈은 있으나 문제 발생")
            all_ok = False
    except Exception:
        logger.error("Playwright: 설치되지 않음 - 'pip install playwright'")
        all_ok = False

    # Playwright 브라우저
    playwright_path = shutil.which("playwright")
    if playwright_path:
        try:
            result = subprocess.run(
                ["playwright", "install", "--dry-run", "chromium"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                logger.success("Playwright 브라우저: chromium")
            else:
                logger.warn("Playwright 브라우저 미설치 - 'playwright install chromium'을 실행하세요")
                all_ok = False
        except Exception:
            logger.warn("Playwright 브라우저 확인 불가")
    else:
        logger.warn("Playwright CLI를 찾을 수 없음 - 'playwright install chromium'을 실행하세요")

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
