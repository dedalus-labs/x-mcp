# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Sample MCP client for testing the x-mcp server."""

import asyncio

from dedalus_mcp.client import MCPClient


SERVER_URL = "http://localhost:8080/mcp"


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

    # Test x_get_user_by_username
    print("--- x_get_user_by_username ---")
    user = await client.call_tool("x_get_user_by_username", {"username": "elonmusk"})
    print(user)
    print()

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
