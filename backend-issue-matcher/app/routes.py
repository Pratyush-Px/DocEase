from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import List, Dict, Any
from app.models.schemas import MatchResponse, MatchInfo
from app.services.resume_parser import parse_resume
from app.services.github_service import fetch_github_issues
from app.services.embedding_service import create_embedding, create_embeddings_batch
from app.services.vector_db_service import (
    get_repo_identifier, is_index_fresh, create_and_save_index, 
    load_index_and_metadata, search_index, get_index_paths
)
from app.services.matcher_service import rank_issues
from app.config import logger
import time

router = APIRouter()

@router.post("/match-issues", response_model=MatchResponse)
async def match_issues(
    repo_url: str = Form(...),
    resume_file: UploadFile = File(...)
):
    start_time = time.time()
    
    # 1. Validate inputs
    if not repo_url.startswith("https://github.com/"):
        raise HTTPException(status_code=400, detail="Invalid GitHub repository URL.")
        
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
        raise HTTPException(status_code=400, detail="Could not extract text from resume.")

    # 3. Create Resume Embedding
    resume_embedding = create_embedding(resume_text)

    # 4. Handle Vector DB (Cache or Build)
    repo_identifier = get_repo_identifier(repo_url)
    index_path, metadata_path = get_index_paths(repo_identifier)
    
    need_refresh = not is_index_fresh(index_path, max_age_hours=24)
    
    if need_refresh:
        logger.info(f"Index for {repo_identifier} is missing or stale. Fetching issues...")
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
                    top_matches=[]
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
            raise HTTPException(status_code=500, detail="Failed to process repository issues.")
    else:
        logger.info(f"Using cached index for {repo_identifier}")
        index, metadata = load_index_and_metadata(repo_identifier)
        if index is None or metadata is None:
            logger.error("Failed to load cached index despite being marked as fresh.")
            raise HTTPException(status_code=500, detail="Failed to load vector database.")

    # 5. Search Index
    try:
        # Search for top 20 nearest neighbors
        distances, indices = search_index(index, resume_embedding, k=20)
        
        # Filter out invalid indices (FAISS returns -1 if there aren't enough items)
        valid_matches = [(distances[i], metadata[idx]) for i, idx in enumerate(indices) if idx != -1 and idx < len(metadata)]
        
        if not valid_matches:
             return MatchResponse(
                user_skills=user_skills,
                repo=repo_identifier.replace("_", "/"),
                issues_scanned=len(metadata),
                top_matches=[]
            )

        candidate_distances = [d for d, m in valid_matches]
        candidate_metadata = [m for d, m in valid_matches]

    except Exception as e:
        logger.error(f"Error searching vector index: {e}")
        raise HTTPException(status_code=500, detail="Failed to search vector database.")

    # 6. Rank Issues using multi-signal scoring
    top_matches = rank_issues(user_skills, candidate_metadata, candidate_distances)
    
    top_match_infos = [
        MatchInfo(
            title=match["title"],
            url=match["url"],
            score=match["score"],
            matched_skills=match["matched_skills"],
            labels=match["labels"]
        ) for match in top_matches
    ]

    elapsed = time.time() - start_time
    logger.info(f"match-issues request completed in {elapsed:.3f} seconds.")

    return MatchResponse(
        user_skills=user_skills,
        repo=repo_identifier.replace("_", "/"),
        issues_scanned=len(metadata),
        top_matches=top_match_infos
    )
