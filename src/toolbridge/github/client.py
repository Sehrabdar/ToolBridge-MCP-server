from typing import Any, TypedDict

import httpx


class GitHubRepository(TypedDict):
    full_name: str
    html_url: str
    description: str | None


class GitHubClientError(Exception):
    """Base exception for Github client errors"""


class GitHubNotFoundError(GitHubClientError):
    """Requested resource does not exist."""


class GitHubRateLimitError(GitHubClientError):
    """Github rate limit exceeded."""


class GitHubAuthError(GitHubClientError):
    """Authentication failed or token lacks required scope."""


class GitHubClient:
    def __init__(self, token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-Github-Api-Version": "2022-11-28",
            },
            timeout=10.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def search_repositories(self, query: str) -> list[GitHubRepository]:
        response = await self._client.get("/search/repositories", params={"q": query})
        if response.status_code in (401, 403):
            raise GitHubAuthError(f"Github auth failed: {response.text}")
        if response.status_code == 429:
            raise GitHubRateLimitError("Github rate limit exceeded")
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        items: list[GitHubRepository] = data["items"]
        return items
