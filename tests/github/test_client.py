import httpx
import pytest
import respx

from toolbridge.github.client import (
    GitHubAuthError,
    GitHubClient,
    GitHubClientError,
    GitHubNotFoundError,
    GitHubRateLimitError,
)


@pytest.mark.anyio
@respx.mock
async def test_search_repositories_returns_items() -> None:
    respx.get("https://api.github.com/search/repositories").mock(
        return_value=httpx.Response(
            200,
            json={"items": [{"full_name": "org/repo", "html_url": "https://github.com/org/repo"}]},
        )
    )
    client = GitHubClient(token="fake-token")
    try:
        results = await client.search_repositories("test")
    finally:
        await client.close()

    assert results == [{"full_name": "org/repo", "html_url": "https://github.com/org/repo"}]


@pytest.mark.anyio
@respx.mock
async def test_search_repositories_raises_auth_error_on_401() -> None:
    respx.get("https://api.github.com/search/repositories").mock(
        return_value=httpx.Response(401, json={"message": "Bad credentials"})
    )
    client = GitHubClient(token="fake-token")
    try:
        with pytest.raises(GitHubAuthError):
            await client.search_repositories("test")
    finally:
        await client.close()


@pytest.mark.anyio
@respx.mock
async def test_search_repositories_raises_rate_limit_error_on_429() -> None:
    respx.get("https://api.github.com/search/repositories").mock(
        return_value=httpx.Response(429, json={"message": "rate limited"})
    )
    client = GitHubClient(token="fake-token")
    try:
        with pytest.raises(GitHubRateLimitError):
            await client.search_repositories("test")
    finally:
        await client.close()


@pytest.mark.anyio
@respx.mock
async def test_list_issues_filters_out_pull_requests() -> None:
    respx.get("https://api.github.com/repos/org/repo/issues").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "number": 1,
                    "title": "Real issue",
                    "state": "open",
                    "html_url": "https://github.com/org/repo/issues/1",
                },
                {
                    "number": 2,
                    "title": "A pull request",
                    "state": "open",
                    "html_url": "https://github.com/org/repo/pull/2",
                    "pull_request": {"url": "https://api.github.com/..."},
                },
            ],
        )
    )
    client = GitHubClient(token="fake-token")
    try:
        issues = await client.list_issues("org/repo")
    finally:
        await client.close()

    assert len(issues) == 1
    assert issues[0]["number"] == 1


@pytest.mark.anyio
@respx.mock
async def test_list_issues_raises_not_found_on_404() -> None:
    respx.get("https://api.github.com/repos/org/nonexistent/issues").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    client = GitHubClient(token="fake-token")
    try:
        with pytest.raises(GitHubNotFoundError):
            await client.list_issues("org/nonexistent")
    finally:
        await client.close()


@pytest.mark.anyio
@respx.mock
async def test_get_file_contents_decodes_base64() -> None:
    import base64

    encoded = base64.b64encode(b"print('hello')").decode("ascii")
    respx.get("https://api.github.com/repos/org/repo/contents/main.py").mock(
        return_value=httpx.Response(
            200,
            json={"path": "main.py", "content": encoded, "encoding": "base64"},
        )
    )
    client = GitHubClient(token="fake-token")
    try:
        result = await client.get_file_contents("org/repo", "main.py")
    finally:
        await client.close()

    assert result == {
        "path": "main.py",
        "content": "print('hello')",
        "encoding": "utf-8",
    }


@pytest.mark.anyio
@respx.mock
async def test_get_file_contents_raises_not_found_on_404() -> None:
    respx.get("https://api.github.com/repos/org/repo/contents/missing.py").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    client = GitHubClient(token="fake-token")
    try:
        with pytest.raises(GitHubNotFoundError):
            await client.get_file_contents("org/repo", "missing.py")
    finally:
        await client.close()


@pytest.mark.anyio
@respx.mock
async def test_get_file_contents_raises_on_directory_path() -> None:
    respx.get("https://api.github.com/repos/org/repo/contents/src").mock(
        return_value=httpx.Response(
            200,
            json=[{"path": "src/main.py", "type": "file"}],  # directory listing, not a file
        )
    )
    client = GitHubClient(token="fake-token")
    try:
        with pytest.raises(GitHubClientError, match="directory"):
            await client.get_file_contents("org/repo", "src")
    finally:
        await client.close()
