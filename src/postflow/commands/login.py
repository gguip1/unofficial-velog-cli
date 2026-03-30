import asyncio

import typer

from postflow.adapters.velog.auth import auth_exists, check_auth, login
from postflow.utils import logger


def login_cmd() -> None:
    """Velog에 로그인합니다."""
    if auth_exists():
        logger.info("기존 세션이 있습니다. 유효한지 확인 중...")
        is_valid = asyncio.run(check_auth())
        if is_valid:
            logger.success("이미 로그인되어 있습니다.")
            relogin = typer.confirm("다시 로그인할까요?", default=False)
            if not relogin:
                return

    logger.info("브라우저가 열립니다. Velog에 로그인해주세요.")
    logger.info("로그인 완료 후 자동으로 세션이 저장됩니다.")

    try:
        asyncio.run(login())
        logger.success("로그인 완료! 세션이 저장되었습니다.")
    except TimeoutError:
        logger.error("로그인 시간이 초과되었습니다. 다시 시도하세요.")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"로그인 실패: {e}")
        raise typer.Exit(1)
