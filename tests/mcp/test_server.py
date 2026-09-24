import httpx
import pytest
import respx

from mcp import Client
from toolbridge.mcp.server import mcp


@pytest.mark.anyio
@respx.mock
async def test_search_repositories_returns_structured_response() -> None:
    respx.get("https://api.github.com/search/repositories").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "full_name": "org/repo",
                        "html_url": "https://github.com/org/repo",
                        "description": "A test repo",
                    }
                ]
            },
        )
    )
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.call_tool("search_repositories", {"query": "fastapi"})
        assert result.structured_content == {
            "query": "fastapi",
            "results": [
                {
                    "name": "org/repo",
                    "url": "https://github.com/org/repo",
                    "description": "A test repo",
                }
            ],
        }


@pytest.mark.anyio
@respx.mock
async def test_list_issues_returns_structured_response() -> None:
    respx.get("https://api.github.com/repos/org/repo/issues").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "number": 42,
                    "title": "Something is broken",
                    "state": "open",
                    "html_url": "https://github.com/org/repo/issues/42",
                }
            ],
        )
    )
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.call_tool("list_issues", {"repo": "org/repo"})
        assert result.structured_content == {
            "repo": "org/repo",
            "issues": [
                {
                    "number": 42,
                    "title": "Something is broken",
                    "state": "open",
                    "url": "https://github.com/org/repo/issues/42",
                }
            ],
        }


@pytest.mark.anyio
async def test_tools_are_discoverable_with_schemas() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools.tools}
        assert tool_names == {
            "search_repositories",
            "list_issues",
            "get_file_contents",
        }


@pytest.mark.anyio
@respx.mock
async def test_get_file_contents_returns_structured_response() -> None:
    import base64

    encoded = base64.b64encode(b"# Hello").decode("ascii")
    respx.get("https://api.github.com/repos/org/repo/contents/README.md").mock(
        return_value=httpx.Response(
            200,
            json={"path": "README.md", "content": encoded, "encoding": "base64"},
        )
    )
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.call_tool(
            "get_file_contents", {"repo": "org/repo", "path": "README.md"}
        )
        assert result.structured_content == {
            "repo": "org/repo",
            "path": "README.md",
            "content": "# Hello",
            "encoding": "utf-8",
        }
