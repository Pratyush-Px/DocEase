# 🔍 Issue Matcher

A NotebookLM-style tool that scrapes GitHub issues from any repository and matches them to your resume using AI — helping you find the **best open source issues to contribute to** based on your skills and experience.

---

## ✨ How It Works

1. **Paste a GitHub repo URL** and **upload your resume** (PDF or plain text)
2. The tool scrapes all open issues from the repo using the GitHub API
3. Your resume is parsed into structured skills and keywords *(1 Gemini call)*
4. All issues + your resume are embedded as vectors *(1 Gemini call)*
5. Cosine similarity is computed **locally** — no extra API calls
6. Top matching issues are explained with contribution suggestions *(1 Gemini call)*

> **Total Gemini API calls per session: 3** — regardless of how many issues exist in the repo.

---

## 📁 Project Structure

```
issue-matcher/
├── backend/
│   ├── main.py                 # FastAPI entry point & route definitions
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # API keys (gitignored — never commit this)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── github_scraper.py   # Fetches open issues from GitHub REST API
│   │   ├── resume_parser.py    # Parses resume into structured JSON (1 Gemini call)
│   │   ├── embedder.py         # Batch embeds issues + resume (1 Gemini call)
│   │   ├── matcher.py          # Cosine similarity matching (local, zero API cost)
│   │   └── explainer.py        # Explains top matches with contribution tips (1 Gemini call)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic request/response models
│   │
│   └── utils/
│       ├── __init__.py
│       └── cache.py            # JSON file-based caching for issue embeddings
│
├── frontend/
│   ├── index.html              # Main UI layout
│   ├── style.css               # Styling
│   └── app.js                  # Vanilla JS logic (no build step needed)
│
└── README.md
```

---

## 🧠 API Usage Strategy

The biggest challenge with LLM-powered tools is **avoiding redundant API calls**. Here's how this project keeps Gemini usage minimal:

| Step | Operation | API Cost |
|------|-----------|----------|
| Scrape GitHub issues | GitHub REST API | Free (60 req/hr unauthenticated) |
| Parse resume | `gemini-1.5-flash` | **1 call** |
| Embed all issues + resume | `text-embedding-004` (batch) | **1 call** |
| Compute similarity | Cosine similarity (NumPy) | Free (local math) |
| Explain top matches | `gemini-1.5-flash` | **1 call** |

### Caching Layer
Issue embeddings are cached locally in a JSON file keyed by:
```
{repo_url} + {latest_issue_updated_at}
```
If you run the tool again on the same repo and no issues have changed, **zero Gemini calls** are made for embedding — the cached vectors are reused directly.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, FastAPI |
| AI / Embeddings | Google Gemini API (`gemini-1.5-flash`, `text-embedding-004`) |
| GitHub Data | GitHub REST API v3 |
| Frontend | Vanilla HTML + CSS + JavaScript |
| Caching | Local JSON file |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)
- (Optional) A [GitHub Personal Access Token](https://github.com/settings/tokens) for higher rate limits

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/issue-matcher.git
cd issue-matcher
```

### 2. Set Up the Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file inside the `backend/` folder:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_github_token_here   # Optional but recommended
```

### 4. Run the Backend
```bash
uvicorn main:app --reload --port 8000
```

### 5. Open the Frontend
Simply open `frontend/index.html` in your browser. No build step needed.

---

## 📌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/match` | Main endpoint — takes repo URL + resume, returns ranked issues |
| `GET` | `/health` | Health check |

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Your Google Gemini API key |
| `GITHUB_TOKEN` | ⚠️ Optional | GitHub PAT — increases rate limit from 60 to 5000 req/hr |

---

## 💡 Tips

- Use the `good first issue` or `help wanted` label filter to reduce the number of issues scraped and keep responses more relevant
- The more detailed your resume, the better the matching quality
- If a repo has 200+ issues, the tool automatically filters to the most recent 100 to stay within embedding limits

---

## 📄 License

MIT License — feel free to use, modify, and distribute.
