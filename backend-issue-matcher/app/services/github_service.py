import asyncio
import httpx
from typing import List, Dict, Any
from app.config import settings, logger
from fastapi import HTTPException


def parse_github_input(input_str: str):
    input_str = input_str.strip()

    # Topic mode
    if input_str.startswith("topic:"):
        return {"type": "topic", "value": input_str.replace("topic:", "").strip()}

    # GitHub URL
    if input_str.startswith("https://github.com/"):
        path = input_str.replace("https://github.com/", "").strip("/")
        parts = path.split("/")

        # Organization
        if len(parts) == 1:
            return {"type": "org", "owner": parts[0]}

        # Repository
        elif len(parts) >= 2:
            return {"type": "repo", "owner": parts[0], "repo": parts[1]}

    raise HTTPException(status_code=400, detail="Invalid GitHub input format")


async def fetch_repo_languages(repo_path: str) -> List[str]:
    """
    Fetches the primary languages used in a GitHub repository.
    Returns a list of language names (e.g., ['JavaScript', 'HTML', 'CSS']).
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    api_url = f"https://api.github.com/repos/{repo_path}/languages"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url, headers=headers)
            if response.status_code == 200:
                # GitHub returns a dict of { "Language": bytes_of_code }
                # We just want the language names
                return list(response.json().keys())
        except Exception as e:
            logger.warning(f"Failed to fetch repo languages for {repo_path}: {e}")

    return []


async def safe_get(client, url, headers, label):
    try:
        resp = await client.get(url, headers=headers)
        return resp.json().get("items", []) if resp.status_code == 200 else []
    except httpx.RequestError as e:
        logger.error(f"Error fetching {label} issues: {e}")
        return []


async def fetch_org_issues(owner: str) -> List[Dict[str, Any]]:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    async with httpx.AsyncClient(follow_redirects=True) as client:
        repos_url = f"https://api.github.com/orgs/{owner}/repos?per_page=10"

        response = await client.get(repos_url, headers=headers)

        if response.status_code != 200:
            raise HTTPException(
                status_code=400, detail="Failed to fetch organization repos"
            )

        repos = response.json()

        async def safe_fetch(repo_url):
            try:
                return await fetch_github_issues(repo_url)
            except Exception:
                return []

        results = await asyncio.gather(
            *[
                safe_fetch(f"https://github.com/{owner}/{repo.get('name')}")
                for repo in repos
            ]
        )

        all_issues = []
        for issues in results:
            all_issues.extend(issues)

        return all_issues[:100]


async def fetch_github_issues(repo_url: str) -> List[Dict[str, Any]]:
    """
    Fetches up to 100 open issues with 'good first issue' label from the specified repo.
    """
    parsed = parse_github_input(repo_url)

    # ORG MODE
    if parsed["type"] == "org":
        return await fetch_org_issues(parsed["owner"])
    if parsed["type"] == "topic":
        return await fetch_topic_issues(parsed["value"])

    # REPO MODE
    if parsed["type"] != "repo":
        raise HTTPException(status_code=400, detail="Invalid input type")

    repo_path = f"{parsed['owner']}/{parsed['repo']}"

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    async with httpx.AsyncClient(follow_redirects=True) as client:
        # First validate the repository exists
        repo_api_url = f"https://api.github.com/repos/{repo_path}"
        try:
            repo_response = await client.get(repo_api_url, headers=headers)
        except httpx.RequestError as e:
            logger.error(f"Error connecting to GitHub API: {e}")
            raise HTTPException(
                status_code=503,
                detail="Service unavailable. Failed to connect to GitHub.",
            )

        if repo_response.status_code == 404:
            logger.warning(f"Repository not found: {repo_path}")
            raise HTTPException(
                status_code=404, detail="Repository not found or inaccessible."
            )
        elif repo_response.status_code == 403:
            logger.warning("GitHub API rate limit exceeded during repo validation.")
            raise HTTPException(
                status_code=403,
                detail="GitHub API rate limit exceeded. Try again later.",
            )
        elif repo_response.status_code != 200:
            logger.error(
                f"GitHub API error: {repo_response.status_code} - {repo_response.text}"
            )
            raise HTTPException(
                status_code=repo_response.status_code,
                detail="Error fetching repository details.",
            )

        base = f"repo:{repo_path}+is:open+is:issue"

        url_a1 = f'https://api.github.com/search/issues?q={base}+label:"good+first+issue"&sort=updated&order=desc&per_page=30'
        url_a2 = f'https://api.github.com/search/issues?q={base}+label:"help+wanted"&sort=updated&order=desc&per_page=30'
        url_b = f"https://api.github.com/search/issues?q={base}&sort=updated&order=desc&per_page=50"

        items_a1, items_a2, items_b = await asyncio.gather(
            safe_get(client, url_a1, headers, "'good first issue'"),
            safe_get(client, url_a2, headers, "'help wanted'"),
            safe_get(client, url_b, headers, "recent"),
        )

        seen_urls = set()
        extracted_issues = []

        for item in items_a1 + items_a2 + items_b:
            if "pull_request" in item or item["html_url"] in seen_urls:
                continue
            seen_urls.add(item["html_url"])
            labels = [l["name"] for l in item.get("labels", [])]
            extracted_issues.append(
                {
                    "title": item.get("title", ""),
                    "description": item.get("body", "") or "",
                    "labels": labels,
                    "url": item["html_url"],
                    "created_at": item.get("created_at", ""),
                    "comments": item.get("comments", 0),
                }
            )

        logger.info(
            f"Fetched {len(extracted_issues)} issues from {repo_path} "
            f"({len(items_a1)} good-first, {len(items_a2)} help-wanted, {len(items_b)} recent)"
        )
        extracted_issues = extracted_issues[:100]
        return extracted_issues


async def fetch_topic_issues(topic: str) -> List[Dict[str, Any]]:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    base = f"topic:{topic}+is:issue+is:open"

    url_a1 = f'https://api.github.com/search/issues?q={base}+label:"good+first+issue"&sort=updated&order=desc&per_page=30'
    url_a2 = f'https://api.github.com/search/issues?q={base}+label:"help+wanted"&sort=updated&order=desc&per_page=30'
    url_b = f"https://api.github.com/search/issues?q={base}&sort=updated&order=desc&per_page=50"

    async with httpx.AsyncClient(follow_redirects=True) as client:
        items_a1, items_a2, items_b = await asyncio.gather(
            safe_get(client, url_a1, headers, "'good first issue' topic"),
            safe_get(client, url_a2, headers, "'help wanted' topic"),
            safe_get(client, url_b, headers, "recent topic"),
        )

        seen_urls = set()
        extracted_issues = []

        for item in items_a1 + items_a2 + items_b:
            if "pull_request" in item or item["html_url"] in seen_urls:
                continue
            seen_urls.add(item["html_url"])
            labels = [l["name"] for l in item.get("labels", [])]
            extracted_issues.append(
                {
                    "title": item.get("title", ""),
                    "description": item.get("body", "") or "",
                    "labels": labels,
                    "url": item["html_url"],
                    "created_at": item.get("created_at", ""),
                    "comments": item.get("comments", 0),
                }
            )

        logger.info(
            f"Fetched {len(extracted_issues)} topic issues for '{topic}' "
            f"({len(items_a1)} good-first, {len(items_a2)} help-wanted, {len(items_b)} recent)"
        )
        extracted_issues = extracted_issues[:100]
        return extracted_issues
