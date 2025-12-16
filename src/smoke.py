# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Minimal tools for local smoke testing.

These tools intentionally avoid `ctx.dispatch(...)` so we can validate:
- SDK serialization + credential encryption
- Product API JIT token exchange + MCP handshake

…without requiring enclave dispatch to be available locally.
"""

from __future__ import annotations

from pydantic import BaseModel

from dedalus_mcp import tool


class SmokePingResponse(BaseModel):
    ok: bool = True
    message: str


@tool(description="Local smoke test tool that does not require enclave dispatch.")
async def smoke_ping(message: str = "pong") -> SmokePingResponse:
    return SmokePingResponse(message=message)


smoke_tools = [smoke_ping]
