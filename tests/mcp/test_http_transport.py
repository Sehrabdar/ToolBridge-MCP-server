import asyncio

import httpx
import pytest
import uvicorn

from mcp import Client
from toolbridge.server.app import create_app


@pytest.mark.anyio
async def test_health_endpoint_unaffected_by_mcp_mount(async_client: httpx.AsyncClient) -> None:
    """The root-level MCP mount must not shadow existing FastAPI routes."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.anyio
async def test_mcp_tools_discoverable_over_real_http() -> None:
    """Confirm the MCP mount actually works end-to-end over a real socket,
    not just in-process — this is the transport-layer proof, distinct from
    the in-process Client(mcp) tests elsewhere in this suite.
    """
    app = create_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=8765, log_level="warning")
    server = uvicorn.Server(config)

    task = asyncio.create_task(server.serve())
    try:
        while not server.started:
            await asyncio.sleep(0.05)

        async with Client("http://127.0.0.1:8765/mcp") as client:
            tools = await client.list_tools()
            tool_names = {tool.name for tool in tools.tools}
            assert tool_names == {
                "search_repositories",
                "list_issues",
                "get_file_contents",
            }
    finally:
        server.should_exit = True
        await task


@pytest.mark.anyio
async def test_calling_unknown_tool_returns_clean_error() -> None:
    app = create_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=8766, log_level="warning")
    server = uvicorn.Server(config)

    task = asyncio.create_task(server.serve())
    try:
        while not server.started:
            await asyncio.sleep(0.05)

        async with Client("http://127.0.0.1:8766/mcp") as client:
            result = await client.call_tool("delete_everything", {})
            assert result.is_error is True
    finally:
        server.should_exit = True
        await task


@pytest.mark.anyio
async def test_raw_request_without_session_id_returns_json_rpc_error() -> None:
    app = create_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=8767, log_level="warning")
    server = uvicorn.Server(config)

    task = asyncio.create_task(server.serve())
    try:
        while not server.started:
            await asyncio.sleep(0.05)

        async with httpx.AsyncClient() as raw_client:
            response = await raw_client.get("http://127.0.0.1:8767/mcp")
            body = response.json()
            assert body["error"]["message"] == "Bad Request: Missing session ID"
    finally:
        server.should_exit = True
        await task
