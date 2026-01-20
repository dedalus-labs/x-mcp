# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

from dedalus_mcp import MCPServer
from dedalus_mcp.server import TransportSecuritySettings

from x import x_api, x_tools


# --- Server ------------------------------------------------------------------

server = MCPServer(
    name="x-mcp",
    connections=[x_api],
    http_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    streamable_http_stateless=True,  # Required for Lambda deployments
)


async def main() -> None:
    server.collect(*x_tools)
    await server.serve(port=8080)
