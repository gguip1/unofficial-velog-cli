from datetime import datetime
from enum import Enum

from pydantic import BaseModel, field_validator


class PostStatus(str, Enum):
    draft = "draft"
    ready = "ready"
    published = "published"


class Visibility(str, Enum):
    public = "public"
    private = "private"


class Meta(BaseModel):
    id: str
    title: str
    slug: str
    description: str = ""
    tags: list[str] = []
    status: PostStatus = PostStatus.draft
    visibility: Visibility = Visibility.public
    series: str | None = None
    thumbnail: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        import re

        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError(
                f"슬러그는 소문자, 숫자, 하이픈만 사용 가능합니다: '{v}'"
            )
        return v
