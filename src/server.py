# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

from dedalus_mcp import MCPServer
from dedalus_mcp.server import TransportSecuritySettings

from db import supabase, db_tools
from gh import github, gh_tools


# --- Server ------------------------------------------------------------------

server = MCPServer(
    name="example-dedalus-mcp",
    connections=[github, supabase],
    http_security=TransportSecuritySettings(enable_dns_rebinding_protection=True)
)


async def main() -> None:
    server.collect(*gh_tools, *db_tools)
    await server.serve()
