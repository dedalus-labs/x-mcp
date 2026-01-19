# X-MCP

A Dedalus MCP server for read-only access to the X (Twitter) API v2.

## Setup

1. Get API credentials from the [X Developer Portal](https://developer.x.com)
2. Copy `.env.example` to `.env` and fill in your credentials:

```
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
```

3. Install dependencies:

```bash
uv sync
```

4. Run the server:

```bash
uv run python -m src.main
```

## Available Tools

### Users
- `x_get_user` - Get a user by their ID
- `x_get_user_by_username` - Get a user by their username
- `x_get_users` - Get multiple users by IDs

### Tweets
- `x_get_tweet` - Get a tweet by its ID
- `x_get_tweets` - Get multiple tweets by IDs
- `x_get_user_tweets` - Get a user's recent tweets
- `x_get_user_mentions` - Get tweets mentioning a user

### Search
- `x_search_recent` - Search tweets from the last 7 days
- `x_count_recent` - Count tweets matching a query

### Followers
- `x_get_followers` - Get a user's followers
- `x_get_following` - Get users a user is following

### Lists
- `x_get_list` - Get a list by its ID
- `x_get_list_tweets` - Get tweets from a list
- `x_get_user_lists` - Get lists owned by a user

## Authentication

This server uses Bearer Token (App-Only) authentication. The server automatically generates a Bearer Token from your API Key and API Secret at startup.

App-Only authentication provides read-only access to public data. Write operations (posting, liking, following) are not supported.

## Rate Limits

Rate limits depend on your X API access tier. See [X API Rate Limits](https://developer.x.com/en/docs/twitter-api/rate-limits) for details.
