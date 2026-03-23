"""
Readiness Service — Contribution Readiness Score

Computes a readiness_score (0–1) that estimates how likely a user
is to successfully solve a given GitHub issue RIGHT NOW.

This is INDEPENDENT of the existing relevance/ranking score.
"""

import re
from typing import Dict, Any, List


# ── Label-based difficulty tiers ──────────────────────────────────────────────

EASY_LABELS = {"good first issue", "beginner", "easy", "starter", "low-hanging fruit"}
MEDIUM_LABELS = {"medium", "intermediate", "help wanted"}
HARD_LABELS = {"hard", "complex", "advanced", "expert"}


def calculate_difficulty_score(issue: Dict[str, Any]) -> float:
    """
    Estimate how difficult the issue is (higher = easier to solve).

    Logic:
    - Easy labels → 1.0
    - Medium labels → 0.6
    - Hard labels → 0.3
    - No difficulty label → heuristic based on comment count:
        - 3–15 comments (healthy discussion) → 0.6
        - >30 comments (likely complex/contested) → 0.3
        - Otherwise → 0.5 (neutral default)
    """
    labels_lower = {label.lower() for label in issue.get("labels", [])}

    if labels_lower & EASY_LABELS:
        return 1.0
    if labels_lower & HARD_LABELS:
        return 0.3
    if labels_lower & MEDIUM_LABELS:
        return 0.6

    # Fallback heuristic: use comment count as a proxy
    comments = issue.get("comments", 0)
    if 3 <= comments <= 15:
        return 0.6
    elif comments > 30:
        return 0.3
    return 0.5


def calculate_clarity_score(issue: Dict[str, Any]) -> float:
    """
    Measure how clear and actionable an issue is (higher = clearer).

    Signals:
    - Description length > 100 chars → base clarity
    - Structured elements (code blocks, bullet points, headers) → bonus
    - Comments present → slight bonus (discussion = more context)
    - Empty/vague description → low score
    """
    description = issue.get("description", "") or ""
    comments = issue.get("comments", 0)

    score = 0.0

    # ── Description length ────────────────────────────────────────────────
    desc_len = len(description)
    if desc_len > 300:
        score += 0.45
    elif desc_len > 100:
        score += 0.30
    elif desc_len > 0:
        score += 0.10
    # else: empty → 0

    # ── Structured content (code blocks, lists, headers) ──────────────────
    structure_patterns = [
        r"```",           # code blocks
        r"^[\-\*] ",      # bullet points
        r"^#{1,6} ",      # markdown headers
        r"\d+\.\s",       # numbered lists
    ]
    structure_hits = sum(
        1 for pat in structure_patterns
        if re.search(pat, description, re.MULTILINE)
    )
    score += min(structure_hits * 0.10, 0.30)

    # ── Comments as supplementary context ─────────────────────────────────
    if comments >= 1:
        score += 0.10
    if comments >= 5:
        score += 0.10

    # Clamp to [0, 1]
    return min(score, 1.0)


def _build_readiness_reason(
    skill_match: float,
    difficulty: float,
    clarity: float,
    recency: float,
) -> str:
    """
    Generate a human-readable explanation for the readiness score.
    """
    parts: List[str] = []

    # Skill match
    if skill_match >= 0.6:
        parts.append("High skill match")
    elif skill_match >= 0.3:
        parts.append("Moderate skill match")
    else:
        parts.append("Low skill match")

    # Difficulty
    if difficulty >= 0.8:
        parts.append("beginner-friendly")
    elif difficulty >= 0.5:
        parts.append("moderate difficulty")
    else:
        parts.append("challenging issue")

    # Clarity
    if clarity >= 0.6:
        parts.append("clear issue description")
    elif clarity >= 0.3:
        parts.append("somewhat clear description")
    else:
        parts.append("vague description")

    # Recency
    if recency >= 0.6:
        parts.append("recently posted")
    elif recency <= 0.2:
        parts.append("older issue")

    return " + ".join(parts)


def calculate_readiness_score(
    issue: Dict[str, Any],
    skill_match_score: float,
    recency_score: float,
) -> Dict[str, Any]:
    """
    Compute the contribution readiness score for a single issue.

    Parameters
    ----------
    issue : dict
        The issue metadata dict (title, description, labels, comments, etc.).
    skill_match_score : float
        Pre-computed skill overlap score (from matcher_service).
        Passed as input to avoid cross-service imports.
    recency_score : float
        Pre-computed recency score (from matcher_service).

    Returns
    -------
    dict with keys:
        - readiness_score : float  (0–1, clamped)
        - readiness_reason : str   (human-readable explanation)
    """
    difficulty = calculate_difficulty_score(issue)
    clarity = calculate_clarity_score(issue)

    readiness = (
        0.40 * skill_match_score
        + 0.20 * difficulty
        + 0.20 * clarity
        + 0.20 * recency_score
    )

    # Safety clamp
    readiness = max(0.0, min(readiness, 1.0))

    reason = _build_readiness_reason(
        skill_match_score, difficulty, clarity, recency_score
    )

    return {
        "readiness_score": round(readiness, 2),
        "readiness_reason": reason,
    }
