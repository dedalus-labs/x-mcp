# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Sample MCP client demonstrating MCP secrets + JIT token exchange.

Environment variables:
    DEDALUS_API_KEY: Your Dedalus API key (dsk_*)
    X_API_KEY: X API Key (Consumer Key)
    X_API_SECRET: X API Secret (Consumer Secret)
    DEDALUS_API_URL: Product API base URL (default: http://localhost:8080)
    DEDALUS_AS_URL: OpenMCP AS base URL used to fetch the encryption public key
                   (default: http://localhost:4444)
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

# Server framework provides Connection/SecretKeys/SecretValues definitions
from dedalus_mcp.auth import SecretValues
from dedalus_mcp import MCPServer
from dedalus_mcp.server import TransportSecuritySettings

# SDK provides client-side encryption + request serialization
from dedalus_labs import AsyncDedalus, DedalusRunner

# Import connection definition from server
from x import x_api

# --- Configuration ------------------------------------------------------------

# Dev environment URLs
API_URL = os.getenv("DEDALUS_API_URL", "http://localhost:8080")
AS_URL = os.getenv("DEDALUS_AS_URL", "http://localhost:4444")

# Auth
DEDALUS_API_KEY = os.getenv("DEDALUS_API_KEY")


# --- Secret Bindings ----------------------------------------------------------
# These provide ACTUAL values for the secrets.

x_secrets = SecretValues(x_api, token=os.getenv("X_BEARER_TOKEN", ""))


# --- MCP Server Definitions ---------------------------------------------------

srv1 = MCPServer(
    name="x-mcp",
    connections=[x_api],
    http_security=TransportSecuritySettings(enable_dns_rebinding_protection=False)
)

# Optional local override: treat this MCPServer instance as a direct URL server.
# This is only for local smoke testing (avoids marketplace lookup for `slug`).
_local_mcp_url = os.getenv("MCP_SERVER_URL")
if _local_mcp_url:
    srv1._serving_url = _local_mcp_url  # type: ignore[attr-defined]

# --- Main ---------------------------------------------------------------------


async def main() -> None:
    client = AsyncDedalus(
        api_key=DEDALUS_API_KEY,
        base_url=API_URL,
        as_base_url=AS_URL,
    )

    runner = DedalusRunner(client)
    result = await runner.run(
        input="Use the X API to get information about the user @elonmusk",
        model="openai/gpt-4o",
        mcp_servers=[srv1],
        credentials=[x_secrets],
    )
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
