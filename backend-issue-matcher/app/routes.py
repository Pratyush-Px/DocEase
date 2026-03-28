from app.models.schemas import ActionPlanRequest, ActionPlanResponse
from app.services.action_plan_service import generate_action_plan_llm
from app.services.github_service import fetch_repo_languages, parse_github_input
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import List, Dict, Any
from app.models.schemas import MatchResponse, MatchInfo
from app.services.resume_parser import parse_resume
from app.services.github_service import fetch_github_issues
from app.services.embedding_service import create_embedding, create_embeddings_batch
from app.services.vector_db_service import (
    get_repo_identifier,
    is_index_fresh,
    create_and_save_index,
    load_index_and_metadata,
    search_index,
    get_index_paths,
)
from app.services.matcher_service import rank_issues
from app.config import logger
import numpy as np
import time
from app.services.contribution_service import get_contributing_text
from app.services.contribution_service import extract_setup_steps
from app.services.contribution_service import generate_contribution_summary
from app.services.repo_health_service import get_repo_health

router = APIRouter()


@router.post("/match-issues", response_model=MatchResponse)
async def match_issues(
    repo_url: str = Form(...),
    resume_file: UploadFile = File(...),
    experience_level: str = Form("junior"),  # NEW: Defaults to junior
):
    start_time = time.time()

    # 1. Validate inputs
    if not (
        repo_url.startswith("https://github.com/") or repo_url.startswith("topic:")
    ):
        raise HTTPException(status_code=400, detail="Invalid GitHub input.")

    if not resume_file.filename:
        raise HTTPException(status_code=400, detail="Missing resume file.")

    # 2. Parse Resume
    try:
        resume_content = await resume_file.read()
        parsed_resume = parse_resume(resume_content)
        user_skills = parsed_resume["skills"]
        resume_text = parsed_resume["text"]
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        raise HTTPException(status_code=400, detail="Failed to parse resume file.")

    if not resume_text:
        raise HTTPException(
            status_code=400, detail="Could not extract text from resume."
        )

    # 3. Create Resume Embedding (with optional skill blending)
    resume_embedding = create_embedding(resume_text)

    if user_skills:
        skills_text = " ".join(user_skills)
        skills_embedding = create_embedding(skills_text)
        blended = 0.30 * np.array(resume_embedding) + 0.70 * np.array(skills_embedding)
        norm = np.linalg.norm(blended)
        if norm > 0:
            blended = blended / norm  # renormalize after blending
        resume_embedding = blended.tolist()

    # 4. Handle Vector DB (Cache or Build)
    repo_identifier = get_repo_identifier(repo_url)
    index_path, metadata_path = get_index_paths(repo_identifier)

    need_refresh = not is_index_fresh(index_path, max_age_hours=24)

    if need_refresh:
        logger.info(
            f"Index for {repo_identifier} is missing or stale. Fetching issues..."
        )
        try:
            # Fetch issues from GitHub API
            issues = await fetch_github_issues(repo_url)

            if not issues:
                logger.warning(f"No valid open issues found for {repo_identifier}")
                # We return an empty match list rather than an error if the repo just has no open issues
                return MatchResponse(
                    user_skills=user_skills,
                    repo=repo_identifier.replace("_", "/"),
                    issues_scanned=0,
                    top_matches=[],
                )

            # Generate embeddings for issues
            issue_texts = [
                f"{issue['title']} {issue['description']} {' '.join(issue['labels'])}"
                for issue in issues
            ]

            logger.info("Creating embeddings for issues...")
            issue_embeddings = create_embeddings_batch(issue_texts)

            # Save index and metadata
            create_and_save_index(repo_identifier, issue_embeddings, issues)

            # Load the newly created index
            index, metadata = load_index_and_metadata(repo_identifier)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error building vector index: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to process repository issues."
            )
    else:
        logger.info(f"Using cached index for {repo_identifier}")
        index, metadata = load_index_and_metadata(repo_identifier)
        if index is None or metadata is None:
            logger.error("Failed to load cached index despite being marked as fresh.")
            raise HTTPException(
                status_code=500, detail="Failed to load vector database."
            )

    # 5. Search Index
    try:
        # Search for top 20 nearest neighbors
        distances, indices = search_index(index, resume_embedding, k=20)

        # Filter out invalid indices (FAISS returns -1 if there aren't enough items)
        valid_matches = [
            (distances[i], metadata[idx])
            for i, idx in enumerate(indices)
            if idx != -1 and idx < len(metadata)
        ]

        if not valid_matches:
            return MatchResponse(
                user_skills=user_skills,
                repo=repo_identifier.replace("_", "/"),
                issues_scanned=len(metadata),
                top_matches=[],
            )

        candidate_distances = [d for d, m in valid_matches]
        candidate_metadata = [m for d, m in valid_matches]

    except Exception as e:
        logger.error(f"Error searching vector index: {e}")
        raise HTTPException(status_code=500, detail="Failed to search vector database.")
    # 5.5 Fetch implicit repository languages for better skill matching
    repo_languages = []
    try:
        parsed_input = parse_github_input(repo_url)
        # We only fetch languages if they provided a specific repo, not a general topic
        if parsed_input["type"] == "repo":
            repo_path = f"{parsed_input['owner']}/{parsed_input['repo']}"
            repo_languages = await fetch_repo_languages(repo_path)
            logger.info(f"Implicit repo languages injected: {repo_languages}")
    except Exception as e:
        logger.warning(f"Could not extract repo languages: {e}")

    # 6. Rank Issues using multi-signal scoring
    # We now pass repo_languages into rank_issues
    top_matches = rank_issues(
        resume_skills=user_skills,
        candidate_issues=candidate_metadata,
        distances=candidate_distances,
        repo_languages=repo_languages,
        experience_level=experience_level,  # <-- ADD THIS LINE HERE!
    )

    top_match_infos = [
        MatchInfo(
            title=match["title"],
            url=match["url"],
            score=match["score"],
            readiness_score=match["readiness_score"],
            readiness_reason=match["readiness_reason"],
            matched_skills=match["matched_skills"],
            labels=match["labels"],
            skill_gap=match.get("skill_gap", ""),
        )
        for match in top_matches
    ]

    elapsed = time.time() - start_time
    logger.info(f"match-issues request completed in {elapsed:.3f} seconds.")

    return MatchResponse(
        user_skills=user_skills,
        repo=repo_identifier.replace("_", "/"),
        issues_scanned=len(metadata),
        top_matches=top_match_infos,
    )


@router.post("/generate-action-plan", response_model=ActionPlanResponse)
async def create_action_plan(request: ActionPlanRequest):
    """
    Generates a step-by-step markdown guide on how to tackle a specific issue.
    """
    plan = generate_action_plan_llm(
        title=request.issue_title,
        description=request.issue_description,
        repo=request.repo_url,
        skills=request.user_skills,
    )

    return ActionPlanResponse(markdown_plan=plan)

@router.post("/contributing")
async def get_contributing(repo_url: str = Form(...)):
    """
    Fetch contributing guidelines for a repository
    """
    try:
        text = await get_contributing_text(repo_url)

        if not text:
            return {
                "repo": repo_url,
                "message": "No contributing guidelines found.",
                "content": ""
            }
    
        setup_steps = extract_setup_steps(text)

        summary = generate_contribution_summary(text)

        return {
            "repo": repo_url,
            "setup_steps": setup_steps,
            "llm_summary": summary,
            "content": text[:1000]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/repo-health")
async def repo_health(repo_url: str = Form(...)):
    try:
        result = await get_repo_health(repo_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))