from typing import List, Dict, Any
from datetime import datetime
import numpy as np
import re

# Weights (rebalanced after review)
WEIGHT_SEMANTIC = 0.50
WEIGHT_SKILL = 0.20
WEIGHT_LABEL = 0.15
WEIGHT_ACTIVITY = 0.10
WEIGHT_RECENCY = 0.05

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
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            if re.search(pattern, text_lower):
                matched += 1
        else:
            if skill_lower in text_lower:
                matched += 1

    return matched / max(len(resume_skills), 1)

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

def rank_issues(resume_skills: List[str], candidate_issues: List[Dict[str, Any]], distances: List[float]) -> List[Dict[str, Any]]:
    """
    Takes candidate issues from FAISS and applies multi-signal ranking.
    Returns the top 5 match objects.
    """
    ranked_issues = []
    resume_skills_set = set(resume_skills)
    
    for i, issue in enumerate(candidate_issues):
        distance = distances[i] if i < len(distances) else 1.0
        
        # Build full issue text for skill matching (not just labels)
        issue_text = f"{issue.get('title', '')} {issue.get('description', '')} {' '.join(issue.get('labels', []))}"
        
        # Calculate individual scores
        semantic_score = calculate_semantic_score(distance)
        skill_score = calculate_skill_overlap_score(resume_skills_set, issue_text)
        label_score = calculate_label_priority_score(issue.get("labels", []))
        activity_score = calculate_activity_score(issue.get("comments", 0))
        recency_score = calculate_recency_score(issue.get("created_at", ""))
        
        # Final weighted score
        final_score = (
            WEIGHT_SEMANTIC * semantic_score +
            WEIGHT_SKILL * skill_score +
            WEIGHT_LABEL * label_score +
            WEIGHT_ACTIVITY * activity_score +
            WEIGHT_RECENCY * recency_score
        )
        
        # Prepare matched skills for the output — match against full text
        matched_skills = [
            skill for skill in resume_skills 
            if skill.lower() in issue_text.lower()
        ]
        
        ranked_issues.append({
            "title": issue.get("title", ""),
            "url": issue.get("url", ""),
            "score": round(final_score, 2),
            "matched_skills": matched_skills,
            "labels": issue.get("labels", [])
        })

    # Sort descending by score
    ranked_issues.sort(key=lambda x: x["score"], reverse=True)
    
    return ranked_issues[:5]
