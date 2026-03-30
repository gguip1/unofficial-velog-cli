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

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not v or v != v.strip():
            raise ValueError(f"슬러그가 비어있거나 공백이 포함되어 있습니다: '{v}'")
        return v
