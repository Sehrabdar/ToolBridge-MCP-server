from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel

from toolbridge.config.settings import get_settings
from toolbridge.github.client import GitHubClient


class RepositoryResult(BaseModel):
    name: str
    url: str
    description: str | None = None


class SearchRepositoriesResult(BaseModel):
    query: str
    results: list[RepositoryResult]


class IssueResult(BaseModel):
    number: int
    title: str
    state: str
    url: str


class ListIssuesResponse(BaseModel):
    repo: str
    issues: list[IssueResult]


class FileContentsResponse(BaseModel):
    repo: str
    path: str
    content: str
    encoding: str


mcp = MCPServer("toolbridge")


@mcp.tool()
async def search_repositories(query: str) -> SearchRepositoriesResult:
    """Search Github repositories by keyword query"""
    settings = get_settings()
    client = GitHubClient(token=settings.github_token)
    try:
        raw_results = await client.search_repositories(query)
    finally:
        await client.close()
    results = [
        RepositoryResult(
            name=item["full_name"],
            url=item["html_url"],
            description=item.get("description"),
        )
        for item in raw_results
    ]
    return SearchRepositoriesResult(query=query, results=results)


if __name__ == "__main__":
    mcp.run()


@mcp.tool()
async def list_issues(repo: str, state: str = "open") -> ListIssuesResponse:
    """List issues for a GitHub repository, optionally filtered by state (open/closed/all)."""
    settings = get_settings()
    client = GitHubClient(token=settings.github_token)
    try:
        raw_issues = await client.list_issues(repo, state=state)
    finally:
        await client.close()
    issues = [
        IssueResult(
            number=item["number"], title=item["title"], state=item["state"], url=item["html_url"]
        )
        for item in raw_issues
    ]
    return ListIssuesResponse(repo=repo, issues=issues)


@mcp.tool()
def get_file_content(repo: str, path: str) -> FileContentsResponse:
    """Retrieve the contents of a file from a GitHub repository."""
    return FileContentsResponse(repo=repo, path=path, content="", encoding="utf-8")
