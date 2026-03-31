import shutil

import typer

from postflow.adapters.velog.auth import POSTFLOW_DIR, auth_exists
from postflow.utils import logger


def logout() -> None:
    """Velog 로그인 세션을 삭제합니다."""
    if not auth_exists():
        logger.info("저장된 세션이 없습니다.")
        return

    confirm = typer.confirm(
        f"세션 데이터를 삭제합니다 ({POSTFLOW_DIR}). 계속할까요?",
        default=True,
    )
    if not confirm:
        return

    shutil.rmtree(POSTFLOW_DIR)
    logger.success("세션이 삭제되었습니다.")
