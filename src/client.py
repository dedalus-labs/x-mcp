# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Sample MCP client for testing the dedalus-mcp-server."""

import asyncio

from dedalus_mcp.client import MCPClient


SERVER_URL = "http://localhost:8001/mcp"


async def main() -> None:
    client = await MCPClient.connect(SERVER_URL)

    # List tools
    result = await client.list_tools()
    print(f"\nAvailable tools ({len(result.tools)}):\n")
    for t in result.tools:
        print(f"  {t.name}")
        if t.description:
            print(f"    {t.description}")
        print()

    # Test gh_list_repos
    print("--- gh_list_repos ---")
    repos = await client.call_tool("gh_list_repos", {"per_page": 3})
    print(repos)
    print()

    # Test gh_get_repo
    print("--- gh_get_repo ---")
    repo = await client.call_tool("gh_get_repo", {"owner": "dedalus-labs", "repo": "openmcp"})
    print(repo)
    print()

    # Test db_select (Supabase)
    print("--- db_select ---")
    rows = await client.call_tool("db_select", {"table": "users", "limit": 3})
    print(rows)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
