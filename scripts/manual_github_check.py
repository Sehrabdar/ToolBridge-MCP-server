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

        print("\n--- issues ---")
        issues = await client.list_issues("react/react", state="open")
        for issue in issues[:5]:
            print(f"#{issue['number']}", "-", issue["title"], f"[{issue['state']}]")

        print("\n--- file contents ---")
        file = await client.get_file_contents("fastapi/fastapi", "README.md")
        print(f"path: {file['path']}")
        print(f"encoding: {file['encoding']}")
        print(file["content"][:300])
    finally:
        await client.close()


asyncio.run(main())
