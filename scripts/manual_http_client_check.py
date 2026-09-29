import asyncio

from mcp import Client


async def main() -> None:
    async with Client("http://localhost:8000/mcp") as client:
        tools = await client.list_tools()
        print("discovered tools:", [t.name for t in tools.tools])

        result = await client.call_tool("search_repositories", {"query": "fastapi"})
        print(result.structured_content)


asyncio.run(main())
