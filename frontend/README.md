# ResumeIssueHunter Frontend

A professional, production-grade React (Vite) frontend for the FastAPI backend `backend-issue-matcher`.

## Setup Instructions

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

## Environment Variables

Copy `.env.example` to `.env` and set the backend URL:

```bash
cp .env.example .env
```

**VITE_API_BASE_URL**: The root URL of the FastAPI backend (default: `http://localhost:8000`). This is used to make API calls instead of hardcoded localhost URLs.

## Features & Pages
- **Home (`/`)**: Upload PDF resume, enter GitHub Repo/Topic URL, choose experience level.
- **Results (`/results`)**: Displays matching issues, skill gaps, action plans, repo health, and contributing guidelines.
- **Panels**:
  - `ActionPlanPanel`: Step-by-step LLM-generated guide for an issue.
  - `ContributingPanel`: Extracted setup steps and LLM summary of contribution guidelines.
  - `RepoHealthPanel`: GitHub repository health score and insights.
