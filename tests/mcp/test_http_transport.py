import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_endpoint_unaffected_by_mcp_mount(async_client: AsyncClient) -> None:
    """The root-level MCP mount must not shadow existing FastAPI routes."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
