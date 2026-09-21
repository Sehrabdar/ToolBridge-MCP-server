import httpx
import pytest
import respx

from toolbridge.github.client import GitHubAuthError, GitHubClient, GitHubRateLimitError


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
