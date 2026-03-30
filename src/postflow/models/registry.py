from datetime import datetime

from pydantic import BaseModel

from postflow.models.meta import PostStatus, Visibility


class ProviderInfo(BaseModel):
    name: str
    post_id: str | None = None
    url: str | None = None


class RegistryEntry(BaseModel):
    id: str
    slug: str
    directory: str
    title: str
    status: PostStatus
    visibility: Visibility
    series: str | None = None
    provider: ProviderInfo | None = None
    last_published_at: datetime | None = None


class Registry(BaseModel):
    posts: list[RegistryEntry] = []
