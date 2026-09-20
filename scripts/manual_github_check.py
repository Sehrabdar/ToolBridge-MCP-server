import asyncio

from toolbridge.config.settings import get_settings
from toolbridge.github.client import GitHubClient


async def main() -> None:
    settings = get_settings()
    client = GitHubClient(token=settings.github_token)
    try:
        results = await client.search_repositories("fastapi")
        for repo in results[:3]:
            print(repo["full_name"], "-", repo["html_url"])
    finally:
        await client.close()


asyncio.run(main())
