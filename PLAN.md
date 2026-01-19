# X-MCP Implementation Plan

## Overview

Build an MCP server for **read-only** access to the X (Twitter) API v2 using Bearer Token (App-Only) authentication.

## Authentication

**Bearer Token (App-Only Auth)**
- Uses API Key + API Secret to generate a Bearer Token
- Or use pre-generated Bearer Token from X Developer Portal
- Simple header injection: `Authorization: Bearer {token}`
- ✅ Works with current dedalus-mcp framework

## What You Can Do (Read-Only)

- Search tweets (recent and full-archive)
- Get tweets by ID
- Get user profiles
- Get user timelines
- Get followers/following lists
- Get lists and list members
- Access public metrics

## What You Cannot Do

- Post/delete tweets
- Like/retweet
- Follow/unfollow
- Send DMs
- Any write operations

---

## Implementation Steps

### Step 1: Update Project Configuration

**File: `pyproject.toml`**
- Change name: `example-dedalus-mcp` → `x-mcp`
- Update description, URLs, keywords

### Step 2: Update Environment Variables

**File: `.env.example`**
```
DEDALUS_API_KEY=
X_BEARER_TOKEN=
```

### Step 3: Create X API Module

**File: `src/x.py`** (replaces `gh.py`)

```python
from dedalus_mcp import HttpMethod, HttpRequest, get_context, tool
from dedalus_mcp.auth import Connection, SecretKeys

# Connection definition
x_api = Connection(
    name="x",
    secrets=SecretKeys(token="X_BEARER_TOKEN"),
    base_url="https://api.x.com/2",
    auth_header_format="Bearer {api_key}",
)

# Helper function
async def _request(method, path, params=None):
    ctx = get_context()
    request = HttpRequest(method=method, path=path)
    response = await ctx.dispatch("x", request)
    return response

# Export
x_tools = [...]
```

### Step 4: Implement Tools

#### User Tools
1. `x_get_me()` - Get authenticated app info (limited in app-only)
2. `x_get_user(user_id)` - Get user by ID
3. `x_get_user_by_username(username)` - Get user by username
4. `x_get_users(user_ids)` - Get multiple users by IDs

#### Tweet Tools
5. `x_get_tweet(tweet_id)` - Get single tweet
6. `x_get_tweets(tweet_ids)` - Get multiple tweets
7. `x_get_user_tweets(user_id, max_results)` - Get user's recent tweets
8. `x_get_user_mentions(user_id, max_results)` - Get user's mentions

#### Search Tools
9. `x_search_recent(query, max_results)` - Search tweets (last 7 days)
10. `x_count_recent(query)` - Count tweets matching query

#### Follower Tools
11. `x_get_followers(user_id, max_results)` - Get user's followers
12. `x_get_following(user_id, max_results)` - Get who user follows

#### List Tools
13. `x_get_list(list_id)` - Get list details
14. `x_get_list_tweets(list_id, max_results)` - Get tweets from a list
15. `x_get_user_lists(user_id)` - Get lists owned by user

### Step 5: Update Server

**File: `src/server.py`**

```python
from dedalus_mcp import MCPServer
from dedalus_mcp.server import TransportSecuritySettings

from x import x_api, x_tools
from smoke import smoke_tools

server = MCPServer(
    name="x-mcp",
    connections=[x_api],
    http_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    authorization_server="https://preview.as.dedaluslabs.ai",
)

async def main() -> None:
    server.collect(*smoke_tools, *x_tools)
    await server.serve(port=8080)
```

### Step 6: Clean Up

- Delete `src/gh.py`
- Delete `src/db.py`
- Update `src/smoke.py` if needed

### Step 7: Update README

Document:
- How to get X API Bearer Token
- Available tools and usage
- Rate limits

---

## X API v2 Endpoints Reference

### Users
- `GET /2/users/:id` - User by ID
- `GET /2/users/by/username/:username` - User by username
- `GET /2/users` - Multiple users by IDs

### Tweets
- `GET /2/tweets/:id` - Tweet by ID
- `GET /2/tweets` - Multiple tweets by IDs
- `GET /2/users/:id/tweets` - User's tweets
- `GET /2/users/:id/mentions` - User's mentions

### Search
- `GET /2/tweets/search/recent` - Recent search (7 days)
- `GET /2/tweets/counts/recent` - Tweet counts

### Follows
- `GET /2/users/:id/followers` - User's followers
- `GET /2/users/:id/following` - Who user follows

### Lists
- `GET /2/lists/:id` - List by ID
- `GET /2/lists/:id/tweets` - Tweets from list
- `GET /2/users/:id/owned_lists` - User's lists

---

## Rate Limits (App-Only)

| Endpoint | Limit |
|----------|-------|
| GET /2/tweets | 300/15min |
| GET /2/users | 300/15min |
| GET /2/tweets/search/recent | 450/15min |
| GET /2/users/:id/tweets | 1500/15min |
| GET /2/users/:id/followers | 15/15min |

---

## File Changes Summary

| File | Action |
|------|--------|
| `pyproject.toml` | Modify - update name/metadata |
| `.env.example` | Modify - X_BEARER_TOKEN |
| `src/x.py` | Create - X API tools |
| `src/server.py` | Modify - use x_api |
| `src/gh.py` | Delete |
| `src/db.py` | Delete |
| `README.md` | Modify - document X API |
