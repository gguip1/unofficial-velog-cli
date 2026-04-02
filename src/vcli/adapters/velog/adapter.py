from dataclasses import dataclass

from vcli.adapters.velog.api import get_current_user, write_post, edit_post
from vcli.adapters.velog.auth import auth_exists, check_auth


@dataclass
class PostData:
    title: str
    body: str
    tags: list[str]
    description: str
    slug: str
    visibility: str
    series: str | None = None


@dataclass
class PublishResult:
    success: bool
    post_id: str | None = None
    url: str | None = None
    error: str | None = None


class VelogAdapter:

    def create(self, post: PostData) -> PublishResult:
        if not auth_exists():
            return PublishResult(success=False, error="로그인이 필요합니다. 'vcli login'을 실행하세요.")

        try:
            user = get_current_user()
            username = user["username"] if user else ""

            result = write_post(
                title=post.title,
                body=post.body,
                tags=post.tags,
                is_private=(post.visibility == "private"),
                url_slug=post.slug,
                description=post.description,
            )

            if result:
                url = f"https://velog.io/@{username}/{result['url_slug']}"
                return PublishResult(success=True, post_id=result["id"], url=url)
            return PublishResult(success=False, error="발행 응답이 비어있습니다.")
        except Exception as e:
            return PublishResult(success=False, error=str(e))

    def update(self, post_id: str, post: PostData) -> PublishResult:
        if not auth_exists():
            return PublishResult(success=False, error="로그인이 필요합니다. 'vcli login'을 실행하세요.")

        try:
            user = get_current_user()
            username = user["username"] if user else ""

            result = edit_post(
                post_id=post_id,
                title=post.title,
                body=post.body,
                tags=post.tags,
                is_private=(post.visibility == "private"),
                url_slug=post.slug,
                description=post.description,
            )

            if result:
                url = f"https://velog.io/@{username}/{result['url_slug']}"
                return PublishResult(success=True, post_id=result["id"], url=url)
            return PublishResult(success=False, error="수정 응답이 비어있습니다.")
        except Exception as e:
            return PublishResult(success=False, error=str(e))
