'''
🥇 Level 1 (current)

✔ Extract from main file

🥈 Level 2 (future)

✔ Follow internal links
✔ fetch linked docs

🥉 Level 3 (advanced)

✔ Use embeddings on docs
✔ semantic search for setup

'''

import httpx
from fastapi import HTTPException
from app.config import settings
import re

import re

def extract_setup_steps(text: str):
    """
    Extract only real command-like patterns (not sentences)
    """

    patterns = [
        r"\bnpm install\b",
        r"\bnpm run [a-zA-Z0-9:_-]+\b",
        r"\byarn install\b",
        r"\bpip install [^\n]+",
        r"\bpython [^\n]+",
        r"\bmake [a-zA-Z0-9_-]+\b",
        r"\bdocker-compose [^\n]+",
        r"\bgit clone [^\n]+",
        r"\bcd [^\n]+"
    ]

    found = []

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.extend(matches)

    return list(set(found))

def extract_owner_repo(repo_url: str):
    """
    Extract owner and repo name from GitHub URL
    """
    try:
        parts = repo_url.replace("https://github.com/", "").strip("/").split("/")
        owner = parts[0]
        repo = parts[1]
        return owner, repo
    except:
        raise ValueError("Invalid GitHub URL format")

async def fetch_contributing_file(owner: str, repo: str) -> str:
    """
    Try multiple locations to find contributing guidelines
    """

    headers = {
        "Accept": "application/vnd.github.v3.raw"
    }

    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    possible_paths = [
        "CONTRIBUTING.md",
        "contributing.md",
        ".github/CONTRIBUTING.md",
        ".github/contributing.md"
    ]

    async with httpx.AsyncClient() as client:
        for path in possible_paths:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                return response.text

        # fallback: try README
        readme_url = f"https://api.github.com/repos/{owner}/{repo}/contents/README.md"
        response = await client.get(readme_url, headers=headers)

        if response.status_code == 200:
            return response.text

        return ""
    
async def get_contributing_text(repo_url: str) -> str:
    """
    Main function to fetch contributing guidelines
    """
    owner, repo = extract_owner_repo(repo_url)
    text = await fetch_contributing_file(owner, repo)
    return text
    