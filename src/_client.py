# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Sample MCP client demonstrating credential provisioning.

Environment variables:
    DEDALUS_API_KEY: Your Dedalus API key (dsk_*)
    GITHUB_TOKEN: GitHub personal access token
    SUPABASE_SECRET_KEY: Supabase service role key
    SUPABASE_URL: Supabase project URL
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

# Server framework provides Connection/Credentials/Credential definitions
from dedalus_mcp.auth import Connection, Credential, Credentials
from dedalus_mcp import MCPServer
from dedalus_mcp.server import TransportSecuritySettings

# SDK provides client with auto-provisioning
from dedalus_labs import AsyncDedalus, DedalusRunner

# --- Configuration ------------------------------------------------------------

# Dev environment URLs
API_URL = os.getenv("DEDALUS_API_URL", "http://localhost:8080")
AS_URL = os.getenv("DEDALUS_AS_URL", "https://preview.as.dedaluslabs.ai")

# Auth
DEDALUS_API_KEY = os.getenv("DEDALUS_API_KEY")


# --- Connection Definitions ---------------------------------------------------
# These define WHAT credentials are needed (schema).
# Typically imported from your MCP server package (e.g., from server import github, supabase)

github = Connection(
    name="github",
    credentials=Credentials(token="GITHUB_TOKEN"),
    base_url="https://api.github.com",
)

supabase = Connection(
    name="supabase",
    credentials=Credentials(key="SUPABASE_SECRET_KEY"),
    base_url=f"{os.getenv('SUPABASE_URL', '')}/rest/v1",
)


# --- Credential Bindings ------------------------------------------------------
# These provide ACTUAL values for the credentials.

github_cred = Credential(github, token=os.getenv("GITHUB_TOKEN", ""))
supabase_cred = Credential(supabase, key=os.getenv("SUPABASE_SECRET_KEY", ""))


# --- MCP Server Definitions ---------------------------------------------------

srv1 = MCPServer(
    name="windsor/example-dedalus-mcp",
    connections=[github, supabase],
    http_security=TransportSecuritySettings(enable_dns_rebinding_protection=False)
)

# --- Main ---------------------------------------------------------------------


async def main() -> None:
    # Just pass credentials - the SDK handles:
    # 1. Client-side encryption (RSA-OAEP + AES-256-GCM)
    # 2. Provisioning to Admin API
    # 3. Token exchange for DPoP-bound JWT with connection handles
    client = AsyncDedalus(
        api_key=DEDALUS_API_KEY,
        base_url=API_URL,
        as_base_url=AS_URL,
        credentials=[github_cred, supabase_cred],
    )

    # First request triggers async provisioning + token exchange
    response = await client.chat.completions.create(
        model="openai/gpt-4.1",
        messages=[{"role": "user", "content": "List my GitHub repos"}],
        mcp_servers=[srv1],
    )
    print(f"Response:\n{response.choices[0].message.content}")

    # Using DedalusRunner for multi-turn with tools
    runner = DedalusRunner(client)
    result = await runner.run(
        input="What tables are in my Supabase database?",
        model="openai/gpt-4.1",
        mcp_servers=[srv1],
    )
    print(f"\nRunner Result:\n{result.output}")


if __name__ == "__main__":
    asyncio.run(main())
