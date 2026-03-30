import asyncio
import webbrowser

import typer

from postflow.adapters.velog.auth import auth_exists, check_auth, login_with_token
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

    # 브라우저에서 Velog 열기
    logger.info("브라우저에서 Velog를 엽니다. 로그인해주세요.")
    webbrowser.open("https://velog.io")

    logger.info("")
    logger.info("로그인 후 토큰을 복사해주세요:")
    logger.info("  1. F12 (개발자 도구) 열기")
    logger.info("  2. Application 탭 > Cookies > https://velog.io")
    logger.info("  3. access_token 값 복사")
    logger.info("  4. refresh_token 값 복사")
    logger.info("")

    access_token = typer.prompt("access_token").strip()
    refresh_token = typer.prompt("refresh_token").strip()

    if not access_token or not refresh_token:
        logger.error("토큰이 비어있습니다.")
        raise typer.Exit(1)

    login_with_token(access_token, refresh_token)

    # 저장된 토큰 검증
    logger.info("토큰을 검증하는 중...")
    is_valid = asyncio.run(check_auth())
    if is_valid:
        logger.success("로그인 완료! 세션이 저장되었습니다.")
    else:
        logger.warn("토큰이 저장되었지만 검증에 실패했습니다. 토큰 값을 다시 확인해주세요.")
