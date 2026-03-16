# ResumeIssueHunter v5.0

A scalable production-ready FastAPI backend that recommends GitHub issues for developers based on their resume. It implements intelligent indexing with a FAISS vector database and a multi-signal ranking algorithm.

## Features
- **Resume Parsing:** Extracts text and categorizes skills from PDF resumes using `PyMuPDF`.
- **Repository-Level Caching:** GitHub issues are converted into vector embeddings using `sentence-transformers` and stored locally in a FAISS index. Ensures fast (<200ms) lookups for cached repositories.
- **Smart Refresh Strategy:** Automatically refreshes the repository issue cache from the GitHub REST API every 24 hours.
- **Async Processing:** Uses `httpx` to fetch GitHub issues asynchronously and includes rate-limit and repository validation handling.
- **Multi-Signal Ranking:** Rather than relying purely on cosine similarity, issues are ranked based on semantic similarity, skill overlaps, priority labels ("good first issue", etc.), activity (comments), and recency.

## Tech Stack
- **Python 3.10+**
- **FastAPI / Uvicorn** for async server capabilities
- **PyMuPDF** for PDF parsing
- **Sentence-Transformers (`all-MiniLM-L6-v2`)** for text embeddings
- **FAISS** for fast vector similarity search
- **HTTPX** for async GitHub API requests

## Setup and Installation

1. **Virtual Environment Setup:**
   ```bash
   python -m venv myenv
   # Windows:
   myenv\Scripts\activate
   # macOS/Linux:
   source myenv/bin/activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration:**
   Copy `.env.example` to `.env` and configure your API tokens (a GitHub token helps avoid rate limits during large fetches).
   ```bash
   cp .env.example .env
   # Edit .env with your keys
   ```

## Running the Application
Start the uvicorn server in reload mode for development:
```bash
uvicorn app.main:app --reload
```
The server will run on `http://127.0.0.1:8000`.

## Example API Request
Endpoint: `POST /match-issues`

Send a `multipart/form-data` request containing the `repo_url` string and the `resume_file` PDF upload.

Using `curl`:
```bash
curl -X POST "http://127.0.0.1:8000/match-issues" \
  -F "repo_url=https://github.com/huggingface/transformers" \
  -F "resume_file=@/path/to/your/resume.pdf"
```

## Architecture Summary
1. The user uploads a PDF and specifies a GitHub repository URL.
2. `resume_parser` extracts text and keywords.
3. The system checks if a fresh FAISS vector index exists for the specified repository (under `data/faiss_index/`).
4. If not, `github_service` efficiently fetches the repository's open issues, embeds them using `embedding_service`, and builds the locally cached `vector_db_service` index.
5. The `vector_db_service` retrieves candidate nearest neighbor issues.
6. The `matcher_service` evaluates candidates via a robust multi-signal algorithm (Semantic, Skill overlap, Label priority, Activity, Recency).
7. Top 5 issues are returned in the JSON response.
