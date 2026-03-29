import requests
from app.config import settings

def ask_coding_question(question: str, issue_title: str = "", issue_description: str = "", repo_url: str = ""):
    """
    Answer coding-related questions using NVIDIA LLM
    """

    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    stream = False

    headers = {
        "Authorization": f"Bearer {settings.nvidia_api_key}",
        "Accept": "text/event-stream" if stream else "application/json"
    }

    prompt = f"""
You are a helpful coding assistant.

The user is working on a GitHub issue.

Repository: {repo_url}
Issue Title: {issue_title}
Issue Description: {issue_description}

User Question:
{question}

Provide a clear and structured answer with:

1. Explanation (simple and beginner-friendly)
2. Code solution (if applicable)
3. Best practices (if relevant)

Keep it concise and practical. Format the answer using markdown with clear headings and code blocks.
"""

    payload = {
        "model": "moonshotai/kimi-k2.5",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 700,
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
            answer = data["choices"][0]["message"]["content"]
            return answer.strip()
        except Exception:
            return "Failed to generate answer. Please try again."