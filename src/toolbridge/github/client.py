from typing import Any, TypedDict

import httpx


class GitHubRepository(TypedDict):
    full_name: str
    html_url: str
    description: str | None


class GitHubIssue(TypedDict):
    number: int
    title: str
    state: str
    html_url: str


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

    async def list_issues(self, repo: str, state: str = "open") -> list[GitHubIssue]:
        """List issues for a repo excluding pull requests.

        GitHub's REST API returns pull requests as part of the issues
        endpoint (a PR is technically a kind of issue in their data model).
        Each raw item includes a "pull_request" key only if it's actually
        a PR — we filter those out so this method returns genuine issues
        only, matching what the tool name promises callers.
        """
        response = await self._client.get(f"/repos/{repo}/issues", params={"state": state})
        if response.status_code == 404:
            raise GitHubNotFoundError(f"Repository not found: {repo}")
        if response.status_code in (401, 403):
            raise GitHubAuthError(f"GitHub Auth failed: {response.text}")
        if response.status_code == 429:
            raise GitHubRateLimitError("GitHub rate limit exceeded.")
        response.raise_for_status()
        data: list[dict[str, Any]] = response.json()
        return [
            {
                "number": item["number"],
                "title": item["title"],
                "state": item["state"],
                "html_url": item["html_url"],
            }
            for item in data
            if "pull_request" not in item
        ]
