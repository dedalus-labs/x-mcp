# x-mcp

A [Dedalus MCP server](https://www.dedaluslabs.ai) for read-only access to the X (Twitter) API v2.

## Features

- **14 read-only tools** for accessing X API v2
- Users: lookup by ID, username, or batch
- Tweets: get single/multiple tweets, user timelines, mentions
- Search: recent tweets (7 days), tweet counts
- Social: followers, following
- Lists: details, tweets, user-owned lists
- Secure Bearer Token authentication via Dedalus enclave

## Available Tools

| Tool | Description |
|------|-------------|
| `x_get_user` | Get a user by their ID |
| `x_get_user_by_username` | Get a user by their username |
| `x_get_users` | Get multiple users by their IDs |
| `x_get_tweet` | Get a tweet by its ID |
| `x_get_tweets` | Get multiple tweets by their IDs |
| `x_get_user_tweets` | Get a user's recent tweets |
| `x_get_user_mentions` | Get tweets mentioning a user |
| `x_search_recent` | Search recent tweets (last 7 days) |
| `x_count_recent` | Count tweets matching a query |
| `x_get_followers` | Get a user's followers |
| `x_get_following` | Get users a user is following |
| `x_get_list` | Get a list by its ID |
| `x_get_list_tweets` | Get tweets from a list |
| `x_get_user_lists` | Get lists owned by a user |

## Requirements

- Python 3.10+
- X API Bearer Token (App-Only authentication)
- Dedalus account

## Setup

1. Clone the repository:
```bash
git clone https://github.com/dedalus-labs/x-mcp.git
cd x-mcp
```

2. Install dependencies:
```bash
uv sync
```

3. Create a `.env` file with your credentials:
```bash
X_BEARER_TOKEN=your_bearer_token_here
```

4. Run the server locally:
```bash
cd src && uv run python main.py
```

## Getting an X Bearer Token

1. Go to the [X Developer Portal](https://developer.x.com/en/portal/dashboard)
2. Create a project and app
3. Generate a Bearer Token (App-Only authentication)
4. Copy the token to your `.env` file

## Usage with Dedalus

This server is available on the [Dedalus Marketplace](https://www.dedaluslabs.ai) with slug `dedalus-labs/x-mcp`.

```python
from dedalus_labs import AsyncDedalus, DedalusRunner
from dedalus_mcp.auth import SecretValues

client = AsyncDedalus(api_key="your_dedalus_api_key")
runner = DedalusRunner(client)

result = await runner.run(
    input="Get information about @elonmusk",
    model="anthropic/claude-sonnet-4-20250514",
    mcp_servers=["dedalus-labs/x-mcp"],
    credentials=[SecretValues(x_api, token="your_x_bearer_token")],
)
```

## Rate Limits

Rate limits depend on your X API access tier. See [X API Rate Limits](https://developer.x.com/en/docs/twitter-api/rate-limits) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.
