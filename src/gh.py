# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""GitHub operations for MCP server.

Required environment variables:
    GITHUB_TOKEN: Personal access token (fine-grained or classic)
    GITHUB_BASE_URL: API base URL (default: https://api.github.com)

Token permissions required:
    Read: actions, actions variables, commit statuses, deployments, discussions,
          environments, issues, metadata, pull requests, secrets
    Read/Write: code, workflows
"""

import os
from typing import Any

from dedalus_mcp import HttpMethod, HttpRequest, get_context, tool
from dedalus_mcp.auth import Connection, SecretKeys
from pydantic import BaseModel

from dotenv import load_dotenv

load_dotenv()

# --- Connection --------------------------------------------------------------

github = Connection(
    name="github",
    secrets=SecretKeys(token="GITHUB_TOKEN"),
    base_url="https://api.github.com",
    auth_header_format="token {api_key}",  # GitHub uses "token <pat>" format
)


# --- Response Models ---------------------------------------------------------


class GitHubResult(BaseModel):
    """Generic GitHub API result."""

    success: bool
    data: Any = None
    error: str | None = None


class UserProfile(BaseModel):
    """GitHub user profile."""

    login: str
    name: str | None = None
    email: str | None = None


class Repository(BaseModel):
    """GitHub repository summary."""

    name: str
    full_name: str
    stars: int
    default_branch: str


class Issue(BaseModel):
    """GitHub issue summary."""

    number: int
    title: str
    state: str
    user: str


class PullRequest(BaseModel):
    """GitHub pull request summary."""

    number: int
    title: str
    state: str
    head: str
    base: str


class Workflow(BaseModel):
    """GitHub Actions workflow."""

    id: int
    name: str
    state: str
    path: str


class WorkflowRun(BaseModel):
    """GitHub Actions workflow run."""

    id: int
    name: str
    status: str
    conclusion: str | None
    head_branch: str


class Deployment(BaseModel):
    """GitHub deployment."""

    id: int
    environment: str
    ref: str
    task: str
    created_at: str


class CommitStatus(BaseModel):
    """Commit status."""

    state: str
    context: str
    description: str | None


class Secret(BaseModel):
    """Repository secret (name only, values never exposed)."""

    name: str
    created_at: str
    updated_at: str


class Environment(BaseModel):
    """Repository environment."""

    id: int
    name: str


class Discussion(BaseModel):
    """GitHub discussion summary."""

    number: int
    title: str
    category: str
    author: str


# --- Helper ------------------------------------------------------------------


async def _request(
    method: HttpMethod,
    path: str,
    body: Any = None,
) -> GitHubResult:
    """Make a GitHub API request."""
    ctx = get_context()
    request = HttpRequest(method=method, path=path, body=body)
    response = await ctx.dispatch("github", request)

    if response.success:
        return GitHubResult(success=True, data=response.response.body)

    msg = response.error.message if response.error else "Request failed"
    return GitHubResult(success=False, error=msg)


# --- User Tools --------------------------------------------------------------


@tool(description="Get authenticated user profile")
async def gh_whoami() -> GitHubResult:
    result = await _request(HttpMethod.GET, "/user")
    if result.success:
        u = result.data
        result.data = {
            "login": u.get("login", ""),
            "name": u.get("name"),
            "email": u.get("email"),
        }
    return result


# --- Repository Tools --------------------------------------------------------


@tool(description="List user repositories")
async def gh_list_repos(per_page: int = 10) -> GitHubResult:
    result = await _request(
        HttpMethod.GET,
        f"/user/repos?per_page={per_page}&sort=updated",
    )
    if result.success and isinstance(result.data, list):
        result.data = [
            {
                "name": r.get("name", ""),
                "full_name": r.get("full_name", ""),
                "stars": r.get("stargazers_count", 0),
                "default_branch": r.get("default_branch", "main"),
            }
            for r in result.data
        ]
    else:
        result.data = []
    return result


@tool(description="Get repository details")
async def gh_get_repo(owner: str, repo: str) -> GitHubResult:
    result = await _request(HttpMethod.GET, f"/repos/{owner}/{repo}")
    if result.success:
        r = result.data
        result.data = {
            "name": r.get("name", ""),
            "full_name": r.get("full_name", ""),
            "stars": r.get("stargazers_count", 0),
            "default_branch": r.get("default_branch", "main"),
        }
    return result


# --- Code Tools (Read/Write) -------------------------------------------------


@tool(description="Get file contents from a repository")
async def gh_get_file(
    owner: str,
    repo: str,
    path: str,
    ref: str | None = None,
) -> GitHubResult:
    url = f"/repos/{owner}/{repo}/contents/{path}"
    if ref:
        url += f"?ref={ref}"
    return await _request(HttpMethod.GET, url)


@tool(description="Create or update a file in a repository")
async def gh_put_file(
    owner: str,
    repo: str,
    path: str,
    content_base64: str,
    message: str,
    branch: str | None = None,
    sha: str | None = None,
) -> GitHubResult:
    """Create or update file. For updates, sha of existing file is required."""
    body: dict[str, Any] = {"message": message, "content": content_base64}
    if branch:
        body["branch"] = branch
    if sha:
        body["sha"] = sha
    return await _request(
        HttpMethod.PUT,
        f"/repos/{owner}/{repo}/contents/{path}",
        body,
    )


@tool(description="Delete a file from a repository")
async def gh_delete_file(
    owner: str,
    repo: str,
    path: str,
    message: str,
    sha: str,
    branch: str | None = None,
) -> GitHubResult:
    body: dict[str, Any] = {"message": message, "sha": sha}
    if branch:
        body["branch"] = branch
    return await _request(
        HttpMethod.DELETE,
        f"/repos/{owner}/{repo}/contents/{path}",
        body,
    )


# --- Issues Tools (Read) -----------------------------------------------------


@tool(description="List issues in a repository")
async def gh_list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    per_page: int = 10,
) -> list[Issue]:
    result = await _request(
        HttpMethod.GET,
        f"/repos/{owner}/{repo}/issues?state={state}&per_page={per_page}",
    )
    if result.success and isinstance(result.data, list):
        return [
            Issue(
                number=i.get("number", 0),
                title=i.get("title", ""),
                state=i.get("state", ""),
                user=i.get("user", {}).get("login", ""),
            )
            for i in result.data
            if "pull_request" not in i  # Exclude PRs
        ]
    return []


@tool(description="Get a specific issue")
async def gh_get_issue(owner: str, repo: str, issue_number: int) -> GitHubResult:
    return await _request(
        HttpMethod.GET,
        f"/repos/{owner}/{repo}/issues/{issue_number}",
    )


# --- Pull Requests Tools (Read) ----------------------------------------------


@tool(description="List pull requests in a repository")
async def gh_list_prs(
    owner: str,
    repo: str,
    state: str = "open",
    per_page: int = 10,
) -> list[PullRequest]:
    result = await _request(
        HttpMethod.GET,
        f"/repos/{owner}/{repo}/pulls?state={state}&per_page={per_page}",
    )
    if result.success and isinstance(result.data, list):
        return [
            PullRequest(
                number=p.get("number", 0),
                title=p.get("title", ""),
                state=p.get("state", ""),
                head=p.get("head", {}).get("ref", ""),
                base=p.get("base", {}).get("ref", ""),
            )
            for p in result.data
        ]
    return []


@tool(description="Get a specific pull request")
async def gh_get_pr(owner: str, repo: str, pr_number: int) -> GitHubResult:
    return await _request(
        HttpMethod.GET,
        f"/repos/{owner}/{repo}/pulls/{pr_number}",
    )


# --- Workflows Tools (Read/Write) --------------------------------------------


@tool(description="List workflows in a repository")
async def gh_list_workflows(owner: str, repo: str) -> list[Workflow]:
    result = await _request(
        HttpMethod.GET,
        f"/repos/{owner}/{repo}/actions/workflows",
    )
    if result.success and isinstance(result.data, dict):
        workflows = result.data.get("workflows", [])
        return [
            Workflow(
                id=w.get("id", 0),
                name=w.get("name", ""),
                state=w.get("state", ""),
                path=w.get("path", ""),
            )
            for w in workflows
        ]
    return []


@tool(description="List workflow runs")
async def gh_list_workflow_runs(
    owner: str,
    repo: str,
    workflow_id: int | None = None,
    per_page: int = 10,
) -> list[WorkflowRun]:
    if workflow_id:
        path = f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs?per_page={per_page}"
    else:
        path = f"/repos/{owner}/{repo}/actions/runs?per_page={per_page}"

    result = await _request(HttpMethod.GET, path)
    if result.success and isinstance(result.data, dict):
        runs = result.data.get("workflow_runs", [])
        return [
            WorkflowRun(
                id=r.get("id", 0),
                name=r.get("name", ""),
                status=r.get("status", ""),
                conclusion=r.get("conclusion"),
                head_branch=r.get("head_branch", ""),
            )
            for r in runs
        ]
    return []


@tool(description="Trigger a workflow dispatch event")
async def gh_dispatch_workflow(
    owner: str,
    repo: str,
    workflow_id: int | str,
    ref: str,
    inputs: dict[str, str] | None = None,
) -> GitHubResult:
    body: dict[str, Any] = {"ref": ref}
    if inputs:
        body["inputs"] = inputs
    return await _request(
        HttpMethod.POST,
        f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
        body,
    )


@tool(description="Cancel a workflow run")
async def gh_cancel_workflow_run(owner: str, repo: str, run_id: int) -> GitHubResult:
    return await _request(
        HttpMethod.POST,
        f"/repos/{owner}/{repo}/actions/runs/{run_id}/cancel",
    )


@tool(description="Re-run a workflow")
async def gh_rerun_workflow(owner: str, repo: str, run_id: int) -> GitHubResult:
    return await _request(
        HttpMethod.POST,
        f"/repos/{owner}/{repo}/actions/runs/{run_id}/rerun",
    )


# --- Actions Variables (Read) ------------------------------------------------


@tool(description="List repository actions variables")
async def gh_list_actions_variables(owner: str, repo: str) -> GitHubResult:
    return await _request(
        HttpMethod.GET,
        f"/repos/{owner}/{repo}/actions/variables",
    )


# --- Secrets (Read - names only) ---------------------------------------------


@tool(description="List repository secrets (names only)")
async def gh_list_secrets(owner: str, repo: str) -> list[Secret]:
    result = await _request(
        HttpMethod.GET,
        f"/repos/{owner}/{repo}/actions/secrets",
    )
    if result.success and isinstance(result.data, dict):
        secrets = result.data.get("secrets", [])
        return [
            Secret(
                name=s.get("name", ""),
                created_at=s.get("created_at", ""),
                updated_at=s.get("updated_at", ""),
            )
            for s in secrets
        ]
    return []


# --- Deployments (Read) ------------------------------------------------------


@tool(description="List deployments")
async def gh_list_deployments(
    owner: str,
    repo: str,
    environment: str | None = None,
    per_page: int = 10,
) -> list[Deployment]:
    path = f"/repos/{owner}/{repo}/deployments?per_page={per_page}"
    if environment:
        path += f"&environment={environment}"

    result = await _request(HttpMethod.GET, path)
    if result.success and isinstance(result.data, list):
        return [
            Deployment(
                id=d.get("id", 0),
                environment=d.get("environment", ""),
                ref=d.get("ref", ""),
                task=d.get("task", ""),
                created_at=d.get("created_at", ""),
            )
            for d in result.data
        ]
    return []


# --- Environments (Read) -----------------------------------------------------


@tool(description="List repository environments")
async def gh_list_environments(owner: str, repo: str) -> list[Environment]:
    result = await _request(
        HttpMethod.GET,
        f"/repos/{owner}/{repo}/environments",
    )
    if result.success and isinstance(result.data, dict):
        envs = result.data.get("environments", [])
        return [
            Environment(id=e.get("id", 0), name=e.get("name", ""))
            for e in envs
        ]
    return []


# --- Commit Statuses (Read) --------------------------------------------------


@tool(description="Get combined status for a ref")
async def gh_get_commit_status(owner: str, repo: str, ref: str) -> GitHubResult:
    return await _request(
        HttpMethod.GET,
        f"/repos/{owner}/{repo}/commits/{ref}/status",
    )


@tool(description="List status checks for a ref")
async def gh_list_commit_statuses(
    owner: str,
    repo: str,
    ref: str,
) -> list[CommitStatus]:
    result = await _request(
        HttpMethod.GET,
        f"/repos/{owner}/{repo}/commits/{ref}/statuses",
    )
    if result.success and isinstance(result.data, list):
        return [
            CommitStatus(
                state=s.get("state", ""),
                context=s.get("context", ""),
                description=s.get("description"),
            )
            for s in result.data
        ]
    return []


# --- Discussions (Read) ------------------------------------------------------


@tool(description="List discussions (via GraphQL)")
async def gh_list_discussions(
    owner: str,
    repo: str,
    per_page: int = 10,
) -> GitHubResult:
    """List discussions using GraphQL API."""
    # Note: Discussions require GraphQL API
    query = """
    query($owner: String!, $repo: String!, $first: Int!) {
      repository(owner: $owner, name: $repo) {
        discussions(first: $first) {
          nodes {
            number
            title
            category { name }
            author { login }
          }
        }
      }
    }
    """
    body = {
        "query": query,
        "variables": {"owner": owner, "repo": repo, "first": per_page},
    }
    # GraphQL endpoint is different
    ctx = get_context()
    request = HttpRequest(method=HttpMethod.POST, path="/graphql", body=body)
    response = await ctx.dispatch("github", request)

    if response.success:
        return GitHubResult(success=True, data=response.response.body)
    msg = response.error.message if response.error else "GraphQL request failed"
    return GitHubResult(success=False, error=msg)


# --- Export ------------------------------------------------------------------

gh_tools = [
    # User
    gh_whoami,
    # Repos
    gh_list_repos,
    gh_get_repo,
    # Code (read/write)
    gh_get_file,
    gh_put_file,
    gh_delete_file,
    # Issues (read)
    gh_list_issues,
    gh_get_issue,
    # Pull Requests (read)
    gh_list_prs,
    gh_get_pr,
    # Workflows (read/write)
    gh_list_workflows,
    gh_list_workflow_runs,
    gh_dispatch_workflow,
    gh_cancel_workflow_run,
    gh_rerun_workflow,
    # Actions variables (read)
    gh_list_actions_variables,
    # Secrets (read - names only)
    gh_list_secrets,
    # Deployments (read)
    gh_list_deployments,
    # Environments (read)
    gh_list_environments,
    # Commit statuses (read)
    gh_get_commit_status,
    gh_list_commit_statuses,
    # Discussions (read)
    gh_list_discussions,
]
