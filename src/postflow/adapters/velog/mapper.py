from postflow.adapters.base import PostData
from postflow.models import Meta


def to_post_data(meta: Meta, content: str) -> PostData:
    """PostFlow의 Meta + content를 어댑터용 PostData로 변환한다."""
    return PostData(
        title=meta.title,
        body=content,
        tags=meta.tags,
        description=meta.description,
        slug=meta.slug,
        visibility=meta.visibility.value,
        series=meta.series,
        thumbnail=meta.thumbnail,
    )
