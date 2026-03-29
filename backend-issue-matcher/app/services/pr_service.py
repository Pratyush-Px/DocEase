import requests
from app.config import settings


def generate_pr_draft(issue_title: str, issue_description: str, solution_description: str, repo_url: str):
    """
    Generate a structured PR draft from issue details
    """

    pr_title = f"Fix: {issue_title}"

    summary = f"This PR addresses the issue: {issue_title}."

    changes = [
        "Implemented the required functionality",
        "Updated relevant files and logic",
        "Ensured compatibility with existing system"
    ]

    testing = [
        "Run the application locally",
        "Verify the issue is resolved",
        "Check for regressions"
    ]

    checklist = [
        " Code compiles successfully",
        " Tests added/updated",
        " Documentation updated",
        " No breaking changes introduced"
    ]

    return {
        "pr_title": pr_title,
        "summary": summary,
        "changes": changes,
        "testing": testing,
        "checklist": checklist
    }

def generate_pr_draft_ai(issue_title: str, issue_description: str,  solution_description: str, repo_url: str):
    """
    Generate PR draft using NVIDIA LLM
    """

    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    stream = False

    headers = {
        "Authorization": f"Bearer {settings.nvidia_api_key}",
        "Accept": "text/event-stream" if stream else "application/json"
    }

    prompt = f"""
You are a professional software developer contributing to the repository {repo_url}.

Generate a clean GitHub Pull Request description using:

Issue Title: {issue_title}
Issue Description: {issue_description}
Solution Implemented: {solution_description}

Structure it as:

Title:
Summary:
Changes Made:
How to Test:
Checklist:

Keep it concise and professional.
"""

    payload = {
        "model": "moonshotai/kimi-k2.5",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 600,
        "temperature": 0.6,
        "top_p": 1.00,
        "stream": stream,
        "chat_template_kwargs": {"thinking": False},
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
            return "Failed to generate pr draft. Please try again."