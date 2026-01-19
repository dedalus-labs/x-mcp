# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""X (Twitter) API operations for MCP server.

Read-only access to the X API v2 using Bearer Token (App-Only) authentication.

Required environment variables:
    X_BEARER_TOKEN: Bearer Token from X Developer Portal
"""

from typing import Any
from urllib.parse import urlencode

from dotenv import load_dotenv
from pydantic import BaseModel

from dedalus_mcp import HttpMethod, HttpRequest, get_context, tool
from dedalus_mcp.auth import Connection, SecretKeys

load_dotenv()


# --- Connection --------------------------------------------------------------

x_api = Connection(
    name="x",
    secrets=SecretKeys(token="X_BEARER_TOKEN"),
    base_url="https://api.x.com/2",
    auth_header_format="Bearer {api_key}",
)


# --- Response Models ---------------------------------------------------------


class XResult(BaseModel):
    """Generic X API result."""

    success: bool
    data: Any = None
    error: str | None = None


class User(BaseModel):
    """X user profile."""

    id: str
    username: str
    name: str
    description: str | None = None
    public_metrics: dict[str, int] | None = None


class Tweet(BaseModel):
    """X tweet/post."""

    id: str
    text: str
    author_id: str | None = None
    created_at: str | None = None
    public_metrics: dict[str, int] | None = None


# --- Helper ------------------------------------------------------------------


async def _request(
    method: HttpMethod,
    path: str,
    params: dict[str, Any] | None = None,
) -> XResult:
    """Make an X API request via the enclave dispatch."""
    ctx = get_context()

    # Build path with query params
    if params:
        query_string = urlencode({k: v for k, v in params.items() if v is not None})
        if query_string:
            path = f"{path}?{query_string}"

    request = HttpRequest(method=method, path=path)
    response = await ctx.dispatch("x", request)

    if response.success:
        return XResult(success=True, data=response.response.body)

    msg = response.error.message if response.error else "Request failed"
    return XResult(success=False, error=msg)


# --- User Tools --------------------------------------------------------------


@tool(description="Get a user by their ID")
async def x_get_user(user_id: str) -> XResult:
    """Get a user's profile by their numeric ID.

    Args:
        user_id: The numeric ID of the user (e.g., "12345678")
    """
    return await _request(
        HttpMethod.GET,
        f"/users/{user_id}",
        params={
            "user.fields": "description,public_metrics,created_at",
        },
    )


@tool(description="Get a user by their username")
async def x_get_user_by_username(username: str) -> XResult:
    """Get a user's profile by their username (handle).

    Args:
        username: The username without @ (e.g., "elonmusk")
    """
    return await _request(
        HttpMethod.GET,
        f"/users/by/username/{username}",
        params={
            "user.fields": "description,public_metrics,created_at",
        },
    )


@tool(description="Get multiple users by their IDs")
async def x_get_users(user_ids: list[str]) -> XResult:
    """Get multiple users by their numeric IDs.

    Args:
        user_ids: List of numeric user IDs (max 100)
    """
    if len(user_ids) > 100:
        return XResult(success=False, error="Maximum 100 user IDs allowed")

    return await _request(
        HttpMethod.GET,
        "/users",
        params={
            "ids": ",".join(user_ids),
            "user.fields": "description,public_metrics,created_at",
        },
    )


# --- Tweet Tools -------------------------------------------------------------


@tool(description="Get a tweet by its ID")
async def x_get_tweet(tweet_id: str) -> XResult:
    """Get a single tweet by its ID.

    Args:
        tweet_id: The numeric ID of the tweet
    """
    return await _request(
        HttpMethod.GET,
        f"/tweets/{tweet_id}",
        params={
            "tweet.fields": "author_id,created_at,public_metrics,entities",
            "expansions": "author_id",
            "user.fields": "username,name",
        },
    )


@tool(description="Get multiple tweets by their IDs")
async def x_get_tweets(tweet_ids: list[str]) -> XResult:
    """Get multiple tweets by their IDs.

    Args:
        tweet_ids: List of numeric tweet IDs (max 100)
    """
    if len(tweet_ids) > 100:
        return XResult(success=False, error="Maximum 100 tweet IDs allowed")

    return await _request(
        HttpMethod.GET,
        "/tweets",
        params={
            "ids": ",".join(tweet_ids),
            "tweet.fields": "author_id,created_at,public_metrics,entities",
            "expansions": "author_id",
            "user.fields": "username,name",
        },
    )


@tool(description="Get a user's recent tweets")
async def x_get_user_tweets(user_id: str, max_results: int = 10) -> XResult:
    """Get a user's recent tweets.

    Args:
        user_id: The numeric ID of the user
        max_results: Number of tweets to return (10-100, default 10)
    """
    max_results = max(10, min(100, max_results))

    return await _request(
        HttpMethod.GET,
        f"/users/{user_id}/tweets",
        params={
            "max_results": str(max_results),
            "tweet.fields": "created_at,public_metrics,entities",
        },
    )


@tool(description="Get tweets mentioning a user")
async def x_get_user_mentions(user_id: str, max_results: int = 10) -> XResult:
    """Get recent tweets mentioning a user.

    Args:
        user_id: The numeric ID of the user
        max_results: Number of tweets to return (10-100, default 10)
    """
    max_results = max(10, min(100, max_results))

    return await _request(
        HttpMethod.GET,
        f"/users/{user_id}/mentions",
        params={
            "max_results": str(max_results),
            "tweet.fields": "author_id,created_at,public_metrics",
            "expansions": "author_id",
            "user.fields": "username,name",
        },
    )


# --- Search Tools ------------------------------------------------------------


@tool(description="Search recent tweets (last 7 days)")
async def x_search_recent(query: str, max_results: int = 10) -> XResult:
    """Search for tweets from the last 7 days.

    Args:
        query: Search query (supports X search operators)
        max_results: Number of results (10-100, default 10)
    """
    max_results = max(10, min(100, max_results))

    return await _request(
        HttpMethod.GET,
        "/tweets/search/recent",
        params={
            "query": query,
            "max_results": str(max_results),
            "tweet.fields": "author_id,created_at,public_metrics,entities",
            "expansions": "author_id",
            "user.fields": "username,name",
        },
    )


@tool(description="Count tweets matching a query (last 7 days)")
async def x_count_recent(query: str) -> XResult:
    """Count tweets matching a query from the last 7 days.

    Args:
        query: Search query (supports X search operators)
    """
    return await _request(
        HttpMethod.GET,
        "/tweets/counts/recent",
        params={
            "query": query,
        },
    )


# --- Follower Tools ----------------------------------------------------------


@tool(description="Get a user's followers")
async def x_get_followers(user_id: str, max_results: int = 100) -> XResult:
    """Get a user's followers.

    Args:
        user_id: The numeric ID of the user
        max_results: Number of followers to return (1-1000, default 100)
    """
    max_results = max(1, min(1000, max_results))

    return await _request(
        HttpMethod.GET,
        f"/users/{user_id}/followers",
        params={
            "max_results": str(max_results),
            "user.fields": "description,public_metrics,created_at",
        },
    )


@tool(description="Get users a user is following")
async def x_get_following(user_id: str, max_results: int = 100) -> XResult:
    """Get users that a user is following.

    Args:
        user_id: The numeric ID of the user
        max_results: Number of users to return (1-1000, default 100)
    """
    max_results = max(1, min(1000, max_results))

    return await _request(
        HttpMethod.GET,
        f"/users/{user_id}/following",
        params={
            "max_results": str(max_results),
            "user.fields": "description,public_metrics,created_at",
        },
    )


# --- List Tools --------------------------------------------------------------


@tool(description="Get a list by its ID")
async def x_get_list(list_id: str) -> XResult:
    """Get details about a list.

    Args:
        list_id: The numeric ID of the list
    """
    return await _request(
        HttpMethod.GET,
        f"/lists/{list_id}",
        params={
            "list.fields": "description,follower_count,member_count,owner_id,created_at",
        },
    )


@tool(description="Get tweets from a list")
async def x_get_list_tweets(list_id: str, max_results: int = 10) -> XResult:
    """Get recent tweets from a list.

    Args:
        list_id: The numeric ID of the list
        max_results: Number of tweets to return (1-100, default 10)
    """
    max_results = max(1, min(100, max_results))

    return await _request(
        HttpMethod.GET,
        f"/lists/{list_id}/tweets",
        params={
            "max_results": str(max_results),
            "tweet.fields": "author_id,created_at,public_metrics",
            "expansions": "author_id",
            "user.fields": "username,name",
        },
    )


@tool(description="Get lists owned by a user")
async def x_get_user_lists(user_id: str, max_results: int = 100) -> XResult:
    """Get lists owned by a user.

    Args:
        user_id: The numeric ID of the user
        max_results: Number of lists to return (1-100, default 100)
    """
    max_results = max(1, min(100, max_results))

    return await _request(
        HttpMethod.GET,
        f"/users/{user_id}/owned_lists",
        params={
            "max_results": str(max_results),
            "list.fields": "description,follower_count,member_count,created_at",
        },
    )


# --- Export ------------------------------------------------------------------

x_tools = [
    # Users
    x_get_user,
    x_get_user_by_username,
    x_get_users,
    # Tweets
    x_get_tweet,
    x_get_tweets,
    x_get_user_tweets,
    x_get_user_mentions,
    # Search
    x_search_recent,
    x_count_recent,
    # Followers
    x_get_followers,
    x_get_following,
    # Lists
    x_get_list,
    x_get_list_tweets,
    x_get_user_lists,
]
