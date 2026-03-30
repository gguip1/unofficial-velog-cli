from playwright.async_api import async_playwright

from postflow.adapters.base import PostData, PublishAdapter, PublishResult
from postflow.adapters.velog.auth import AUTH_FILE, auth_exists, check_auth, login
from postflow.adapters.velog.publisher import create_post, update_post


class VelogAdapter(PublishAdapter):

    @property
    def name(self) -> str:
        return "velog"

    async def check_auth(self) -> bool:
        return await check_auth()

    async def login(self) -> None:
        await login()

    async def create(self, post: PostData) -> PublishResult:
        if not auth_exists():
            return PublishResult(success=False, error="로그인이 필요합니다. 'postflow login'을 실행하세요.")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(storage_state=str(AUTH_FILE))
            page = await context.new_page()

            result = await create_post(page, post)

            await browser.close()
            return result

    async def update(self, post_id: str, post: PostData) -> PublishResult:
        if not auth_exists():
            return PublishResult(success=False, error="로그인이 필요합니다. 'postflow login'을 실행하세요.")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(storage_state=str(AUTH_FILE))
            page = await context.new_page()

            result = await update_post(page, post_id, post)

            await browser.close()
            return result
