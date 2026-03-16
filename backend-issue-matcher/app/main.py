from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
from app.config import logger

app = FastAPI(
    title="ResumeIssueHunter v5.0",
    description="Scalable FastAPI backend for recommending GitHub issues based on resumes.",
    version="5.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this to the frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting ResumeIssueHunter API...")

@app.get("/")
def read_root():
    return {"message": "Welcome to ResumeIssueHunter v5.0 API. Use POST /match-issues to get recommendations."}
