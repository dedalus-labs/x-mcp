# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Supabase database operations for MCP server.

Common CRUD operations exposed as MCP tools. Uses Supabase REST API via
dedalus-mcp's HTTP dispatch.

Required environment variables:
    SUPABASE_URL: Project URL (e.g., https://xxx.supabase.co)
    SUPABASE_SECRET_KEY: Supabase service role key (bypasses RLS)
"""

import os
from typing import Any

from dedalus_mcp import HttpMethod, HttpRequest, get_context, tool
from dedalus_mcp.auth import Connection, SecretKeys
from pydantic import BaseModel, Field

from dotenv import load_dotenv

load_dotenv()

# --- Connection --------------------------------------------------------------

supabase = Connection(
    name="supabase",
    secrets=SecretKeys(key="SUPABASE_SECRET_KEY"),
    base_url=f"{os.getenv('SUPABASE_URL')}/rest/v1",
    auth_header_name="apikey",      # Supabase uses 'apikey' header
    auth_header_format="{api_key}",  # Raw value, no Bearer prefix
)


# --- Response Models ---------------------------------------------------------


class DatabaseResult(BaseModel):
    """Generic database operation result."""

    success: bool
    data: list[dict[str, Any]] = Field(default_factory=list)
    count: int | None = None
    error: str | None = None


class DatabaseSingleResult(BaseModel):
    """Single row result."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


# --- Helper ------------------------------------------------------------------


def _headers(prefer: str | None = None) -> dict[str, str]:
    """Build headers for Supabase REST API.

    Note: Authorization header is injected by the framework.
    apikey is required by Supabase for routing even when using service_role key.
    """
    key = os.getenv("SUPABASE_SECRET_KEY", "")
    h: dict[str, str] = {"Content-Type": "application/json", "apikey": key}
    if prefer:
        h["Prefer"] = prefer
    return h


# --- CRUD Tools --------------------------------------------------------------


@tool(description="Select rows from a table with optional filters")
async def db_select(
    table: str,
    columns: str = "*",
    filters: str | None = None,
    order: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DatabaseResult:
    """Query rows from a Supabase table.

    Args:
        table: Table name.
        columns: Columns to select (default "*").
        filters: PostgREST filter string (e.g., "status=eq.active").
        order: Order by column (e.g., "created_at.desc").
        limit: Max rows to return.
        offset: Rows to skip.

    Returns:
        DatabaseResult: Result of the database operation.

    """
    ctx = get_context()

    path = f"/{table}?select={columns}"
    if filters:
        path += f"&{filters}"
    if order:
        path += f"&order={order}"
    if limit:
        path += f"&limit={limit}"
    if offset:
        path += f"&offset={offset}"

    request = HttpRequest(method=HttpMethod.GET, path=path, headers=_headers("count=exact"))
    response = await ctx.dispatch("supabase", request)

    if response.success:
        body = response.response.body
        data = body if isinstance(body, list) else [body] if body else []
        return DatabaseResult(success=True, data=data, count=len(data))

    msg = response.error.message if response.error else "Query failed"
    return DatabaseResult(success=False, error=msg)


@tool(description="Insert one or more rows into a table")
async def db_insert(table: str, rows: list[dict[str, Any]], *, return_data: bool = True) -> DatabaseResult:
    """Insert rows into a Supabase table.

    Args:
        table: Table name.
        rows: List of row objects to insert.
        return_data: Whether to return inserted rows.

    Returns:
        DatabaseResult: Result of the database operation.

    """
    ctx = get_context()

    prefer = "return=representation" if return_data else "return=minimal"
    request = HttpRequest(method=HttpMethod.POST, path=f"/{table}", headers=_headers(prefer), body=rows)
    response = await ctx.dispatch("supabase", request)

    if response.success:
        body = response.response.body
        data = body if isinstance(body, list) else [body] if body else []
        return DatabaseResult(success=True, data=data, count=len(rows))

    msg = response.error.message if response.error else "Insert failed"
    return DatabaseResult(success=False, error=msg)


@tool(description="Update rows in a table matching filters")
async def db_update(table: str, updates: dict[str, Any], filters: str, *, return_data: bool = True) -> DatabaseResult:
    """Update rows in a Supabase table.

    Args:
        table: Table name.
        updates: Fields to update.
        filters: PostgREST filter (required, e.g., "id=eq.123").
        return_data: Whether to return updated rows.

    Returns:
        DatabaseResult: Result of the database operation.

    """
    ctx = get_context()

    prefer = "return=representation" if return_data else "return=minimal"
    request = HttpRequest(method=HttpMethod.PATCH, path=f"/{table}?{filters}", headers=_headers(prefer), body=updates)
    response = await ctx.dispatch("supabase", request)

    if response.success:
        body = response.response.body
        data = body if isinstance(body, list) else [body] if body else []
        return DatabaseResult(success=True, data=data, count=len(data))

    msg = response.error.message if response.error else "Update failed"
    return DatabaseResult(success=False, error=msg)


@tool(description="Delete rows from a table matching filters")
async def db_delete(table: str, filters: str, *, return_data: bool = False) -> DatabaseResult:
    """Delete rows from a Supabase table.

    Args:
        table: Table name.
        filters: PostgREST filter (required, e.g., "id=eq.123").
        return_data: Whether to return deleted rows.

    Returns:
        DatabaseResult: Result of the database operation.

    """
    ctx = get_context()

    prefer = "return=representation" if return_data else "return=minimal"
    request = HttpRequest(method=HttpMethod.DELETE, path=f"/{table}?{filters}", headers=_headers(prefer))
    response = await ctx.dispatch("supabase", request)

    if response.success:
        body = response.response.body
        data = body if isinstance(body, list) else [body] if body else []
        return DatabaseResult(success=True, data=data)

    msg = response.error.message if response.error else "Delete failed"
    return DatabaseResult(success=False, error=msg)


@tool(description="Upsert (insert or update) rows in a table")
async def db_upsert(
    table: str, rows: list[dict[str, Any]], *, on_conflict: str = "id", return_data: bool = True
) -> DatabaseResult:
    """Upsert rows into a Supabase table.

    Args:
        table: Table name.
        rows: List of row objects.
        on_conflict: Conflict resolution column (default "id").
        return_data: Whether to return upserted rows.

    Returns:
        DatabaseResult: Result of the database operation.

    """
    ctx = get_context()

    prefer = "return=representation" if return_data else "return=minimal"
    prefer += ",resolution=merge-duplicates"
    request = HttpRequest(
        method=HttpMethod.POST, path=f"/{table}?on_conflict={on_conflict}", headers=_headers(prefer), body=rows
    )
    response = await ctx.dispatch("supabase", request)

    if response.success:
        body = response.response.body
        data = body if isinstance(body, list) else [body] if body else []
        return DatabaseResult(success=True, data=data, count=len(rows))

    msg = response.error.message if response.error else "Upsert failed"
    return DatabaseResult(success=False, error=msg)


@tool(description="Get a single row by primary key")
async def db_get_by_id(table: str, id_column: str, id_value: str | int, columns: str = "*") -> DatabaseSingleResult:
    """Fetch a single row by ID.

    Args:
        table: Table name.
        id_column: Primary key column name.
        id_value: Primary key value.
        columns: Columns to select.

    Returns:
        DatabaseSingleResult: Result of the database operation.

    """
    ctx = get_context()

    request = HttpRequest(
        method=HttpMethod.GET,
        path=f"/{table}?select={columns}&{id_column}=eq.{id_value}",
        headers=_headers("return=representation"),
    )
    response = await ctx.dispatch("supabase", request)

    if response.success:
        body = response.response.body
        if isinstance(body, list) and body:
            return DatabaseSingleResult(success=True, data=body[0])
        if isinstance(body, dict):
            return DatabaseSingleResult(success=True, data=body)
        return DatabaseSingleResult(success=False, error="Not found")

    msg = response.error.message if response.error else "Query failed"
    return DatabaseSingleResult(success=False, error=msg)


@tool(description="Call a Supabase RPC function")
async def db_rpc(function_name: str, params: dict[str, Any] | None = None) -> DatabaseResult:
    """Call a Supabase stored procedure/function.

    Args:
        function_name: Name of the RPC function.
        params: Parameters to pass to the function.

    Returns:
        DatabaseResult: Result of the database operation.

    """
    ctx = get_context()

    request = HttpRequest(method=HttpMethod.POST, path=f"/rpc/{function_name}", headers=_headers(), body=params or {})
    response = await ctx.dispatch("supabase", request)

    if response.success:
        body = response.response.body
        data = body if isinstance(body, list) else [body] if body else []
        return DatabaseResult(success=True, data=data)

    msg = response.error.message if response.error else "RPC call failed"
    return DatabaseResult(success=False, error=msg)


# --- Export -------------------------------------------------------------------

# Tools to be collected by server
db_tools = [db_select, db_insert, db_update, db_delete, db_upsert, db_get_by_id, db_rpc]
