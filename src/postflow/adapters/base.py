from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PostData:
    title: str
    body: str
    tags: list[str]
    description: str
    slug: str
    visibility: str
    series: str | None = None
    thumbnail: str | None = None


@dataclass
class PublishResult:
    success: bool
    post_id: str | None = None
    url: str | None = None
    error: str | None = None


class PublishAdapter(ABC):

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def check_auth(self) -> bool: ...

    @abstractmethod
    async def login(self) -> None: ...

    @abstractmethod
    async def create(self, post: PostData) -> PublishResult: ...

    @abstractmethod
    async def update(self, post_id: str, post: PostData) -> PublishResult: ...
