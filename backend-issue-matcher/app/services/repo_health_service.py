import httpx
from datetime import datetime
from app.config import settings
from app.services.contribution_service import extract_owner_repo

async def fetch_repo_details(owner: str, repo: str):
    url = f"https://api.github.com/repos/{owner}/{repo}"

    headers = {}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

        if response.status_code != 200:
            return None

        return response.json()

def generate_health_insights(data, score):
    insights = []

    stars = data.get("stargazers_count", 0)
    forks = data.get("forks_count", 0)
    issues = data.get("open_issues_count", 0)

    # Popularity
    if stars > 1000:
        insights.append("Highly popular repository with strong community interest.")
    elif stars > 100:
        insights.append("Moderately popular repository.")
    else:
        insights.append("Less popular, may be niche or new.")

    # Contribution activity
    if forks > 500:
        insights.append("Strong contributor base and active development.")
    elif forks > 100:
        insights.append("Decent community engagement.")
    else:
        insights.append("Limited contributor activity.")

    # Issues interpretation (fixed logic)
    if issues > 500:
        insights.append("Large number of issues — indicates active usage but possible maintenance load.")
    elif issues > 100:
        insights.append("Moderate number of issues — normal for growing projects.")
    else:
        insights.append("Low number of issues — could be stable or less active.")

    # Final summary
    if score >= 7:
        summary = "This repository is highly active and suitable for contributions."
    elif score >= 4:
        summary = "This repository is moderately healthy with contribution opportunities."
    else:
        summary = "This repository may require deeper evaluation before contributing."

    return {
        "insights": insights,
        "summary": summary
    }

def compute_repo_health(data):
    score = 0

    stars = data.get("stargazers_count", 0)
    if stars > 500:
        score += 2
    elif stars > 100:
        score += 1

    forks = data.get("forks_count", 0)
    if forks > 100:
        score += 2
    elif forks > 30:
        score += 1

    issues = data.get("open_issues_count", 0)
    if issues < 50:
        score += 2
    elif issues < 200:
        score += 1

    updated_at = data.get("updated_at")
    if updated_at:
        updated_date = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
        days = (datetime.utcnow() - updated_date).days

        if days < 30:
            score += 2
        elif days < 90:
            score += 1

    return score

async def get_repo_health(repo_url: str):
    owner, repo = extract_owner_repo(repo_url)

    data = await fetch_repo_details(owner, repo)
    if not data:
        return {"error": "Failed to fetch repo"}

    score = compute_repo_health(data)

    insights_data = generate_health_insights(data, score)

    return {
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "last_updated": data["updated_at"],
        "health_score": score,

        "insights": insights_data["insights"],
        "summary": insights_data["summary"]
    }