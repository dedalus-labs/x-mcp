# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Sample MCP client demonstrating MCP secrets + JIT token exchange.

Environment variables:
    DEDALUS_API_KEY: Your Dedalus API key (dsk_*)
    GITHUB_TOKEN: GitHub personal access token
    SUPABASE_SECRET_KEY: Supabase service role key
    SUPABASE_URL: Supabase project URL
    DEDALUS_API_URL: Product API base URL (default: http://localhost:8080)
    DEDALUS_AS_URL: OpenMCP AS base URL used to fetch the encryption public key
                   (default: http://localhost:4444)
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

# Server framework provides Connection/SecretKeys/SecretValues definitions
from dedalus_mcp.auth import Connection, SecretKeys, SecretValues
from dedalus_mcp import MCPServer
from dedalus_mcp.server import TransportSecuritySettings

# SDK provides client-side encryption + request serialization
from dedalus_labs import AsyncDedalus, DedalusRunner

# --- Configuration ------------------------------------------------------------

# Dev environment URLs
API_URL = os.getenv("DEDALUS_API_URL", "http://localhost:8080")
AS_URL = os.getenv("DEDALUS_AS_URL", "http://localhost:4444")

# Auth
DEDALUS_API_KEY = os.getenv("DEDALUS_API_KEY")


# --- Connection Definitions ---------------------------------------------------
# These define WHAT secrets are needed (schema).
# Typically imported from your MCP server package (e.g., from server import github, supabase)

github = Connection(
    name="github",
    secrets=SecretKeys(token="GITHUB_TOKEN"),
    base_url="https://api.github.com",
)

supabase = Connection(
    name="supabase",
    secrets=SecretKeys(key="SUPABASE_SECRET_KEY"),
    base_url=f"{os.getenv('SUPABASE_URL', '')}/rest/v1",
)


# --- Secret Bindings ----------------------------------------------------------
# These provide ACTUAL values for the secrets.

github_secrets = SecretValues(github, token=os.getenv("GITHUB_TOKEN", ""))
supabase_secrets = SecretValues(supabase, key=os.getenv("SUPABASE_SECRET_KEY", ""))


# --- MCP Server Definitions ---------------------------------------------------

srv1 = MCPServer(
    name="windsor/example-dedalus-mcp",
    connections=[github, supabase],
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
        input="Use the Supabase tool to list all tables in the database.",
        model="openai/gpt-4.1",
        mcp_servers=[srv1],
        credentials=[github_secrets, supabase_secrets],
    )
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
