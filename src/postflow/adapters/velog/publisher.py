from playwright.async_api import Page

from postflow.adapters.base import PostData, PublishResult


async def create_post(page: Page, post: PostData) -> PublishResult:
    """Velog 글 작성 페이지에서 새 글을 발행한다."""
    try:
        await page.goto("https://velog.io/write", wait_until="domcontentloaded", timeout=15000)

        # 제목 입력
        title_input = page.locator('textarea[placeholder="제목을 입력하세요"]')
        await title_input.fill(post.title)

        # 본문 입력 (CodeMirror 에디터)
        editor = page.locator(".CodeMirror")
        await editor.click()
        await page.keyboard.press("Control+a")
        await page.keyboard.type(post.body, delay=1)

        # 태그 입력
        if post.tags:
            tag_input = page.locator('input[placeholder="태그를 입력하세요"]')
            for tag in post.tags:
                await tag_input.fill(tag)
                await tag_input.press("Enter")

        # 출간하기 버튼
        publish_btn = page.locator('button:has-text("출간하기")')
        await publish_btn.click()

        # 출간 설정 다이얼로그 대기
        await page.wait_for_selector('.publish-screen', timeout=5000)

        # 설명(description) 입력
        if post.description:
            desc_input = page.locator('textarea[placeholder="당신의 포스트를 짧게 소개해보세요."]')
            await desc_input.fill(post.description)

        # 공개/비공개 설정
        if post.visibility == "private":
            private_btn = page.locator('button:has-text("비공개")')
            await private_btn.click()

        # URL 슬러그 설정
        slug_input = page.locator('.publish-screen input[type="text"]')
        if await slug_input.count() > 0:
            await slug_input.fill(post.slug)

        # 시리즈 설정
        if post.series:
            series_btn = page.locator('button:has-text("시리즈에 추가하기")')
            if await series_btn.count() > 0:
                await series_btn.click()
                series_input = page.locator('input[placeholder="시리즈를 입력하세요"]')
                if await series_input.count() > 0:
                    await series_input.fill(post.series)
                    # 기존 시리즈 선택 또는 새 시리즈 생성
                    series_item = page.locator(f'text="{post.series}"')
                    if await series_item.count() > 0:
                        await series_item.click()

        # 최종 출간 버튼
        final_publish = page.locator('.publish-screen button:has-text("출간하기")')
        await final_publish.click()

        # 발행 후 리다이렉트 대기
        await page.wait_for_url("**/velog.io/@**", timeout=15000)

        url = page.url
        # URL에서 post_id 추출은 어려우므로 URL 자체를 반환
        return PublishResult(success=True, url=url)

    except Exception as e:
        return PublishResult(success=False, error=str(e))


async def update_post(page: Page, post_url: str, post: PostData) -> PublishResult:
    """기존 글의 편집 페이지에서 글을 수정한다."""
    try:
        # 글 편집 페이지로 이동
        edit_url = post_url.replace("velog.io/@", "velog.io/write?id=") if "write?id=" not in post_url else post_url

        # 실제로는 Velog의 편집 URL 패턴을 따라야 함
        # velog.io/write?id=<post-uuid> 형태
        await page.goto(edit_url, wait_until="domcontentloaded", timeout=15000)

        # 제목 수정
        title_input = page.locator('textarea[placeholder="제목을 입력하세요"]')
        await title_input.fill("")
        await title_input.fill(post.title)

        # 본문 수정
        editor = page.locator(".CodeMirror")
        await editor.click()
        await page.keyboard.press("Control+a")
        await page.keyboard.type(post.body, delay=1)

        # 출간하기 버튼 (수정 시에도 동일)
        publish_btn = page.locator('button:has-text("출간하기")')
        await publish_btn.click()

        # 출간 설정에서 수정 후 출간
        await page.wait_for_selector('.publish-screen', timeout=5000)

        if post.description:
            desc_input = page.locator('textarea[placeholder="당신의 포스트를 짧게 소개해보세요."]')
            await desc_input.fill(post.description)

        final_publish = page.locator('.publish-screen button:has-text("출간하기")')
        await final_publish.click()

        await page.wait_for_url("**/velog.io/@**", timeout=15000)

        return PublishResult(success=True, url=page.url)

    except Exception as e:
        return PublishResult(success=False, error=str(e))
