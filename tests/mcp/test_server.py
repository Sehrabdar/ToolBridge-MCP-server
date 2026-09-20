import pytest
 
from mcp import Client
from toolbridge.mcp.server import mcp


@pytest.mark.anyio
async def test_search_repositories_return_structured_response() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.call_tool("search_repositories", {"query": "fastapi"})
        assert result.structured_content == {"query": "fastapi", "results": []}


@pytest.mark.anyio
async def test_list_issues_returns_structured_response() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.call_tool("list_issues", {"repo": "org/repo"})
        assert result.structured_content == {"repo": "org/repo", "issues": []}


@pytest.mark.anyio
async def test_get_file_content_returns_structured_response() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.call_tool(
            "get_file_content", {"repo": "org/repo", "path": "README.md"}
        )
        assert result.structured_content == {
            "repo": "org/repo",
            "path": "README.md",
            "content": "",
            "encoding": "utf-8",
        }


@pytest.mark.anyio
async def test_tools_are_discoverable_with_schemas() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools.tools}
        assert tool_names == {
            "search_repositories",
            "list_issues",
            "get_file_content",
        }
