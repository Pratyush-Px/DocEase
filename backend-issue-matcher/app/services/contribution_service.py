import httpx
from fastapi import HTTPException
from app.config import settings
import re
import requests
from app.config import settings

def extract_code_blocks(text: str):
    import re
    return re.findall(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)

def extract_setup_steps(text: str):
    import re

    steps = []

    # 🔹 Step A: extract from code blocks (PRIMARY)
    code_blocks = extract_code_blocks(text)

    for block in code_blocks:
        lines = block.split("\n")

        for line in lines:
            line = line.strip().lstrip("$").strip()

            if any(cmd in line.lower() for cmd in [
                "git clone", "pip install", "cd ", "npm install",
                "make", "python", "docker", "./", "scripts/install"
            ]):
                steps.append(line)

    # 🔹 Step B: fallback (if no steps found)
    if not steps:
        for line in text.split("\n"):
            line = line.strip()

            if any(cmd in line.lower() for cmd in [
                "git clone", "pip install", "cd ", "npm install"
            ]):
                steps.append(line)

    # 🔹 Step C: clean + deduplicate
    cleaned = []
    for step in steps:
        step = re.sub(r"`|\\$|#", "", step).strip()
        if len(step) > 5:
            cleaned.append(step)

    return list(dict.fromkeys(cleaned))[:8]

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

def extract_relevant_sections(text: str) -> str:
    """
    Extract important sections related to setup, installation, and contribution workflow
    """

    keywords = [
        "setup",
        "install",
        "installation",
        "getting started",
        "development",
        "workflow",
        "contributing",
        "how to",
        "build",
        "run"
    ]

    lines = text.split("\n")
    selected = []

    for line in lines:
        for key in keywords:
            if key.lower() in line.lower():
                selected.append(line.strip())

    # Remove duplicates
    selected = list(set(selected))

    # Fallback if nothing found
    if not selected:
        return text[:1500]

    return "\n".join(selected[:100])

def generate_contribution_summary(text: str) -> str:
    """
    Uses NVIDIA model to summarize contribution guidelines
    """
    filtered_text = extract_relevant_sections(text)


    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    stream = False
    
    headers = {
    "Authorization": f"Bearer {settings.nvidia_api_key}",
    "Accept": "text/event-stream" if stream else "application/json"
    }

    payload = {
    "model": "moonshotai/kimi-k2.5",
    "messages": [{"role":"user","content":f"Summarize the contribution guide into: 1. Setup Steps 2. Contribution Workflow. Keep it clear and structured in bullet points.\n{filtered_text}"}],
    "max_tokens": 500,
    "temperature": 0.6,
    "top_p": 1.00,
    "stream": stream,
    "chat_template_kwargs": {"thinking":False},
    }



    response = requests.post(invoke_url, headers=headers, json=payload)

    if response.status_code != 200:
        return f"LLM API Error (status {response.status_code}): {response.text or 'No response'}"

    if stream:
        for line in response.iter_lines():
            if line:
                return line.decode("utf-8")
    else:
        data = response.json()

        try:
            summary = data["choices"][0]["message"]["content"]
            return summary.strip()
        except Exception:
            return "Summary unavailable. Please try again."