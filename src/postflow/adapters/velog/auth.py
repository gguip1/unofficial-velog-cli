import json
from pathlib import Path

from playwright.async_api import async_playwright, Playwright

POSTFLOW_DIR = Path.home() / ".postflow"
AUTH_FILE = POSTFLOW_DIR / "velog-auth.json"

# Chrome → Edge → Playwright Chromium 순으로 시도
BROWSER_CHANNELS = ["chrome", "msedge", None]


def get_auth_path() -> Path:
    return AUTH_FILE


def auth_exists() -> bool:
    return AUTH_FILE.exists()


async def _launch_browser(p: Playwright, headless: bool = False):
    """사용 가능한 브라우저를 찾아서 실행한다."""
    for channel in BROWSER_CHANNELS:
        try:
            return await p.chromium.launch(channel=channel, headless=headless)
        except Exception:
            continue
    raise RuntimeError(
        "사용 가능한 브라우저를 찾을 수 없습니다.\n"
        "Chrome, Edge 중 하나를 설치하거나 'playwright install chromium'을 실행하세요."
    )


async def check_auth() -> bool:
    """저장된 세션이 유효한지 확인한다."""
    if not AUTH_FILE.exists():
        return False

    try:
        async with async_playwright() as p:
            browser = await _launch_browser(p, headless=True)
            context = await browser.new_context(storage_state=str(AUTH_FILE))
            page = await context.new_page()
            await page.goto("https://velog.io", wait_until="domcontentloaded", timeout=15000)

            try:
                await page.wait_for_selector('button[data-testid="header-user-menu"]', timeout=5000)
                await browser.close()
                return True
            except Exception:
                await browser.close()
                return False
    except Exception:
        return False


def login_with_token(access_token: str, refresh_token: str) -> None:
    """사용자가 직접 복사한 토큰으로 세션을 저장한다."""
    POSTFLOW_DIR.mkdir(parents=True, exist_ok=True)

    storage = {
        "cookies": [
            {
                "name": "access_token",
                "value": access_token,
                "domain": ".velog.io",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax",
            },
            {
                "name": "refresh_token",
                "value": refresh_token,
                "domain": ".velog.io",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax",
            },
        ],
        "origins": [],
    }

    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(storage, f)
