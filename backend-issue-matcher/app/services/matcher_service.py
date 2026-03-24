from typing import List, Dict, Any
from datetime import datetime
import numpy as np
import re
import json

from app.config import logger
from app.services.gemini_client import get_model
from app.services.readiness_service import calculate_readiness_score


def get_persona_weights(experience_level: str):
    """Dynamically adjusts ranking weights based on user seniority."""
    level = experience_level.lower()

    if level == "senior":
        # Seniors don't need beginner labels. Prioritize pure semantic match and recency.
        return {
            "semantic": 0.60,
            "skill": 0.30,
            "label": 0.00,
            "activity": 0.05,
            "recency": 0.05,
        }
    elif level == "mid":
        # Mid-level wants a balance, slightly favoring skill overlap.
        return {
            "semantic": 0.55,
            "skill": 0.25,
            "label": 0.05,
            "activity": 0.10,
            "recency": 0.05,
        }
    else:
        # Junior (default): Needs high clarity, good labels, and moderate activity (existing discussion helps).
        return {
            "semantic": 0.45,
            "skill": 0.20,
            "label": 0.20,
            "activity": 0.10,
            "recency": 0.05,
        }


# Graduated Label Weights
LABEL_WEIGHTS = {
    "good first issue": 1.0,
    "beginner": 1.0,
    "easy": 0.9,
    "starter": 0.9,
    "help wanted": 0.85,
    "low-hanging fruit": 0.85,
    "documentation": 0.7,
}


def generate_skill_gaps_batch(
    resume_skills: list[str], top_issues: list[dict]
) -> list[str]:
    try:
        model = get_model()
        issues_block = "\n".join(
            [
                f"{i+1}. {issue['title']}: {(issue.get('description') or '')[:200]}"
                for i, issue in enumerate(top_issues)
            ]
        )
        prompt = (
            f"A developer has these skills: {', '.join(resume_skills[:15])}\n\n"
            f"Here are 5 GitHub issues they may contribute to:\n"
            f"{issues_block}\n\n"
            f"For each issue write exactly one sentence: what specific skill or knowledge gap should they prepare for, or what makes them well-suited if no gap exists. Be concrete, not generic.\n"
            f"Each response must be under 25 words.\n"
            f"Return ONLY a valid JSON array of exactly 5 strings in the same order as the issues. No explanation, no markdown.\n"
            f'Example: \'["gap or fit for issue 1", "gap or fit for issue 2", ...]\''
        )
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.2},
            request_options={"timeout": 10},
        )
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", response.text, re.DOTALL)
            result = json.loads(match.group()) if match else []
        if not isinstance(result, list):
            result = []
        return (result + [""] * 5)[:5]
    except Exception as e:
        logger.warning(f"Gemini skill gap batch failed: {e}")
        return [""] * 5


def calculate_semantic_score(distance: float) -> float:
    """
    For normalized embeddings with L2 index:
    L2_squared = 2 * (1 - cosine_similarity)
    So: cosine_similarity = 1 - L2_squared / 2

    FAISS IndexFlatL2 returns squared L2 distances directly,
    so this formula is both correct and exact.
    """
    return max(0.0, 1.0 - (distance / 2.0))


def calculate_skill_overlap_score(resume_skills: set, issue_text: str) -> float:
    """
    Matches resume skills against the full issue text (title + description + labels),
    not just labels. Uses word-boundary regex to avoid false positives.
    """
    if not resume_skills:
        return 0.0

    text_lower = issue_text.lower()

    matched = 0
    for skill in resume_skills:
        skill_lower = skill.lower()
        # Use word boundary for short skills to avoid false matches
        # e.g. "go" shouldn't match "google"
        if len(skill_lower) <= 3:
            pattern = r"\b" + re.escape(skill_lower) + r"\b"
            if re.search(pattern, text_lower):
                matched += 1
        else:
            if skill_lower in text_lower:
                matched += 1

    # Cap denominator at 15 to avoid penalizing broad skill sets
    effective_denominator = min(len(resume_skills), 15)
    return min(matched / 2.0, 1.0)


def calculate_label_priority_score(issue_labels: List[str]) -> float:
    """
    Graduated label scoring instead of binary 1.0/0.5.
    Uses a weighted label dictionary for finer differentiation.
    """
    labels_lower = {l.lower() for l in issue_labels}

    scores = [LABEL_WEIGHTS[l] for l in labels_lower if l in LABEL_WEIGHTS]
    return max(scores) if scores else 0.3


def calculate_activity_score(comments_count: int) -> float:
    """
    Inverted U-curve: 3-15 comments is the sweet spot (well-discussed but not contentious).
    Very high comment counts often mean stale/contested issues.
    """
    if comments_count <= 15:
        return comments_count / 15.0
    else:
        return max(0.3, 1.0 - (comments_count - 15) / 50.0)


def calculate_recency_score(created_at_str: str) -> float:
    """
    Softer decay over 180 days (was 60). Issues older than 6 months
    still get a small floor score of 0.1.
    """
    if not created_at_str:
        return 0.0

    try:
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        now = datetime.now(created_at.tzinfo)
        days_old = (now - created_at).days

        return max(0.1, 1.0 - (days_old / 180.0))

    except Exception:
        return 0.0


# Update the function signature to accept repo_languages
def rank_issues(
    resume_skills: List[str],
    candidate_issues: List[Dict[str, Any]],
    distances: List[float],
    repo_languages: List[str] = None,
    experience_level: str = "junior",  # NEW ARGUMENT
) -> List[Dict[str, Any]]:

    ranked_issues = []
    resume_skills_set = set(resume_skills)
    weights = get_persona_weights(experience_level)  # FETCH DYNAMIC WEIGHTS

    if repo_languages is None:
        repo_languages = []
    implicit_context = " ".join(repo_languages)

    for i, issue in enumerate(candidate_issues):
        distance = distances[i] if i < len(distances) else 1.0
        issue_text = f"{issue.get('title', '')} {issue.get('description', '')} {' '.join(issue.get('labels', []))} {implicit_context}"

        semantic_score = calculate_semantic_score(distance)
        skill_score = calculate_skill_overlap_score(resume_skills_set, issue_text)
        label_score = calculate_label_priority_score(issue.get("labels", []))
        activity_score = calculate_activity_score(issue.get("comments", 0))
        recency_score = calculate_recency_score(issue.get("created_at", ""))

        # APPLY DYNAMIC WEIGHTS HERE
        final_score = (
            weights["semantic"] * semantic_score
            + weights["skill"] * skill_score
            + weights["label"] * label_score
            + weights["activity"] * activity_score
            + weights["recency"] * recency_score
        )

        # Prepare matched skills for the output — mirror scoring logic exactly
        matched_skills = []
        for skill in resume_skills:
            skill_lower = skill.lower()
            if len(skill_lower) <= 3:
                pattern = r"\b" + re.escape(skill_lower) + r"\b"
                if re.search(pattern, issue_text.lower()):
                    matched_skills.append(skill)
            else:
                if skill_lower in issue_text.lower():
                    matched_skills.append(skill)

        # Compute readiness score (independent of ranking)
        readiness_result = calculate_readiness_score(
            issue=issue,
            skill_match_score=skill_score,
            recency_score=recency_score,
        )

        ranked_issues.append(
            {
                "title": issue.get("title", ""),
                "url": issue.get("url", ""),
                "score": round(final_score, 2),
                "readiness_score": readiness_result["readiness_score"],
                "readiness_reason": readiness_result["readiness_reason"],
                "matched_skills": matched_skills,
                "labels": issue.get("labels", []),
            }
        )

    # Sort descending by score
    ranked_issues.sort(key=lambda x: x["score"], reverse=True)

    top5 = ranked_issues[:5]
    try:
        gaps = generate_skill_gaps_batch(list(resume_skills_set), top5)
    except Exception:
        gaps = [""] * 5

    for i, issue in enumerate(top5):
        issue["skill_gap"] = gaps[i]

    return top5
