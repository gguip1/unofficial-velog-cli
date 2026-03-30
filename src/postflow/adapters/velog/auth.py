import json
from pathlib import Path

from playwright.async_api import async_playwright

POSTFLOW_DIR = Path.home() / ".postflow"
AUTH_FILE = POSTFLOW_DIR / "velog-auth.json"


def get_auth_path() -> Path:
    return AUTH_FILE


def auth_exists() -> bool:
    return AUTH_FILE.exists()


async def check_auth() -> bool:
    """저장된 세션이 유효한지 확인한다."""
    if not AUTH_FILE.exists():
        return False

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=str(AUTH_FILE))
            page = await context.new_page()
            await page.goto("https://velog.io", wait_until="domcontentloaded", timeout=15000)

            # 로그인 상태 확인: 헤더의 사용자 메뉴 존재 여부
            try:
                await page.wait_for_selector('button[data-testid="header-user-menu"]', timeout=5000)
                await browser.close()
                return True
            except Exception:
                await browser.close()
                return False
    except Exception:
        return False


async def login() -> None:
    """브라우저를 열어 사용자가 직접 로그인하도록 한다."""
    POSTFLOW_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://velog.io", wait_until="domcontentloaded")

        # 사용자가 로그인할 때까지 대기
        # 로그인 후 헤더에 사용자 메뉴 버튼이 나타남
        try:
            await page.wait_for_selector(
                'button[data-testid="header-user-menu"]',
                timeout=300000,  # 5분
            )
        except Exception:
            await browser.close()
            raise TimeoutError("로그인 시간이 초과되었습니다. 다시 시도하세요.")

        # 세션 저장
        storage = await context.storage_state()
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump(storage, f)

        await browser.close()
