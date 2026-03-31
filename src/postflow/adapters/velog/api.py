import json
import urllib.error
from pathlib import Path
from urllib.request import Request, urlopen

from postflow.adapters.velog.auth import AUTH_FILE

VELOG_GRAPHQL = "https://v3.velog.io/graphql"


def _get_access_token() -> str:
    with open(AUTH_FILE, encoding="utf-8") as f:
        storage = json.load(f)
    cookies = {c["name"]: c["value"] for c in storage.get("cookies", [])}
    return cookies.get("access_token", "")


def _graphql(query: str, variables: dict | None = None) -> dict:
    access_token = _get_access_token()
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    req = Request(
        VELOG_GRAPHQL,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Cookie": f"access_token={access_token}",
        },
    )
    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read()
            if not body:
                return {}
            return json.loads(body)
    except urllib.error.URLError as e:
        raise ConnectionError(
            f"Velog API에 연결할 수 없습니다. 네트워크 상태를 확인하세요.\n원인: {e}"
        )
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise PermissionError(
                "인증이 만료되었습니다. 'postflow login'으로 다시 로그인하세요."
            )
        raise ConnectionError(f"Velog API 오류 (HTTP {e.code}): {e.reason}")


def get_current_user() -> dict | None:
    result = _graphql("{ currentUser { id username } }")
    return result.get("data", {}).get("currentUser")


def get_user_posts(username: str) -> list[dict]:
    """사용자의 모든 글을 가져온다."""
    query = """query {
        posts(input: { username: "%s" }) {
            id title url_slug tags is_private
            released_at short_description body
            series { id name }
        }
    }""" % username

    result = _graphql(query)
    return result.get("data", {}).get("posts", [])


def write_post(
    title: str,
    body: str,
    tags: list[str],
    is_private: bool = False,
    url_slug: str = "",
    description: str = "",
    series_id: str | None = None,
) -> dict | None:
    """새 글을 발행한다."""
    query = """mutation WritePost($input: WritePostInput!) {
        writePost(input: $input) {
            id title url_slug
        }
    }"""
    variables = {
        "input": {
            "title": title,
            "body": body,
            "tags": tags,
            "is_markdown": True,
            "is_temp": False,
            "is_private": is_private,
            "url_slug": url_slug,
            "meta": {"short_description": description},
        }
    }
    if series_id:
        variables["input"]["series_id"] = series_id

    result = _graphql(query, variables)
    if "errors" in result:
        raise RuntimeError(result["errors"][0].get("message", str(result["errors"])))
    return result.get("data", {}).get("writePost")


def edit_post(
    post_id: str,
    title: str,
    body: str,
    tags: list[str],
    is_private: bool = False,
    url_slug: str = "",
    description: str = "",
    series_id: str | None = None,
) -> dict | None:
    """기존 글을 수정한다."""
    query = """mutation EditPost($input: EditPostInput!) {
        editPost(input: $input) {
            id title url_slug
        }
    }"""
    variables = {
        "input": {
            "id": post_id,
            "title": title,
            "body": body,
            "tags": tags,
            "is_markdown": True,
            "is_temp": False,
            "is_private": is_private,
            "url_slug": url_slug,
            "meta": {"short_description": description},
        }
    }
    if series_id:
        variables["input"]["series_id"] = series_id

    result = _graphql(query, variables)
    if "errors" in result:
        raise RuntimeError(result["errors"][0].get("message", str(result["errors"])))
    return result.get("data", {}).get("editPost")


def upload_image(file_path: Path) -> str:
    """이미지를 Velog에 업로드하고 URL을 반환한다.
    1. create-url로 S3 signed URL을 받는다
    2. signed URL에 이미지를 PUT으로 업로드한다
    3. image_path(최종 URL)를 반환한다
    """
    import mimetypes

    access_token = _get_access_token()
    filename = file_path.name
    content_type = mimetypes.guess_type(filename)[0] or "image/png"

    # 1단계: signed URL 요청
    create_req = Request(
        "https://v2.velog.io/api/v2/files/create-url",
        data=json.dumps({"type": "post", "filename": filename}).encode(),
        headers={
            "Content-Type": "application/json",
            "Cookie": f"access_token={access_token}",
        },
    )
    try:
        with urlopen(create_req, timeout=15) as resp:
            result = json.loads(resp.read())
    except Exception as e:
        raise ConnectionError(f"이미지 업로드 URL 요청 실패: {e}")

    signed_url = result.get("signed_url")
    image_path = result.get("image_path")
    if not signed_url or not image_path:
        raise RuntimeError("이미지 업로드 URL을 받지 못했습니다.")

    # 2단계: S3에 이미지 업로드
    image_data = file_path.read_bytes()
    put_req = Request(
        signed_url,
        data=image_data,
        headers={"Content-Type": content_type},
        method="PUT",
    )
    try:
        with urlopen(put_req, timeout=30) as resp:
            pass
    except Exception as e:
        raise ConnectionError(f"이미지 업로드 실패: {e}")

    return image_path
