from pydantic import BaseModel
from typing import List

class MatchInfo(BaseModel):
    title: str
    url: str
    score: float
    matched_skills: List[str]
    labels: List[str]

class MatchResponse(BaseModel):
    user_skills: List[str]
    repo: str
    issues_scanned: int
    top_matches: List[MatchInfo]
