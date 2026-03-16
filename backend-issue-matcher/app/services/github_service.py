import httpx
from typing import List, Dict, Any
from app.config import settings, logger
from fastapi import HTTPException

async def fetch_github_issues(repo_url: str) -> List[Dict[str, Any]]:
    """
    Fetches up to 100 open issues with 'good first issue' label from the specified repo.
    """
    repo_path = repo_url.replace("https://github.com/", "").strip("/")
    
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
            raise HTTPException(status_code=503, detail="Service unavailable. Failed to connect to GitHub.")

        if repo_response.status_code == 404:
            logger.warning(f"Repository not found: {repo_path}")
            raise HTTPException(status_code=404, detail="Repository not found or inaccessible.")
        elif repo_response.status_code == 403:
            logger.warning("GitHub API rate limit exceeded during repo validation.")
            raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded. Try again later.")
        elif repo_response.status_code != 200:
            logger.error(f"GitHub API error: {repo_response.status_code} - {repo_response.text}")
            raise HTTPException(status_code=repo_response.status_code, detail="Error fetching repository details.")

        # Search for valid issues. We broaden the search to get any open issues
        # because not all repos use the 'good first issue' label. The ranking
        # algorithm will naturally prioritize beginner-friendly labels.
        search_query = f"repo:{repo_path} is:open is:issue"
        # Sort by updated to get the freshest active issues
        search_url = f"https://api.github.com/search/issues?q={search_query}&sort=updated&order=desc&per_page=100"
        
        try:
            issues_response = await client.get(search_url, headers=headers)
        except httpx.RequestError as e:
             logger.error(f"Error connecting to GitHub API: {e}")
             raise HTTPException(status_code=503, detail="Service unavailable. Failed to connect to GitHub.")

        if issues_response.status_code == 403:
            logger.warning("GitHub API rate limit exceeded during issue fetching.")
            raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded. Try again later.")
        elif issues_response.status_code != 200:
             logger.error(f"GitHub API error fetching issues: {issues_response.status_code} - {issues_response.text}")
             raise HTTPException(status_code=issues_response.status_code, detail="Error fetching issues.")

        data = issues_response.json()
        issues = data.get("items", [])
        
        extracted_issues = []
        for issue in issues:
            # We don't want pull requests
            if "pull_request" in issue:
                continue
                
            labels = [label["name"] for label in issue.get("labels", [])]
            
            extracted_issues.append({
                "title": issue.get("title", ""),
                "description": issue.get("body", "") or "", # Sometimes body is None
                "labels": labels,
                "url": issue.get("html_url", ""),
                "created_at": issue.get("created_at", ""),
                "comments": issue.get("comments", 0)
            })
            
        logger.info(f"Fetched {len(extracted_issues)} open issues from {repo_path}")
        return extracted_issues
