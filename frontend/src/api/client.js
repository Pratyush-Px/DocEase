import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: BASE_URL });

export async function matchIssues({ resumeFile, repoUrl, experienceLevel }) {
  const form = new FormData();
  form.append('resume_file', resumeFile);
  form.append('repo_url', repoUrl);
  form.append('experience_level', experienceLevel);
  const { data } = await api.post('/match-issues', form);
  return data;
}

export async function generateActionPlan({ issueTitle, issueDescription, repoUrl, userSkills }) {
  const { data } = await api.post('/generate-action-plan', {
    issue_title: issueTitle,
    issue_description: issueDescription,
    repo_url: repoUrl,
    user_skills: userSkills,
  });
  return data; // { markdown_plan: "..." }
}

export async function getContributing(repoUrl) {
  const form = new FormData();
  form.append('repo_url', repoUrl);
  const { data } = await api.post('/contributing', form);
  return data; // { setup_steps, llm_summary, content }
}

export async function getRepoHealth(repoUrl) {
  const form = new FormData();
  form.append('repo_url', repoUrl);
  const { data } = await api.post('/repo-health', form);
  return data; // { stars, forks, open_issues, health_score, insights, summary }
}
