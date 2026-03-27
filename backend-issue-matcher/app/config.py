import os
import logging
from pydantic_settings import BaseSettings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    github_token: str = ""
    gemini_api_key: str = ""
    nvidia_api_key: str = ""
    faiss_index_dir: str = "data/faiss_index"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Ensure FAISS index directory exists
os.makedirs(settings.faiss_index_dir, exist_ok=True)

if not settings.github_token:
    logger.warning(
        "GITHUB_TOKEN is not set. GitHub API requests will be unauthenticated. "
        "Search results are capped at 30 per page instead of 100. "
        "Set GITHUB_TOKEN in .env for best results."
    )
else:
    logger.info("GitHub token detected. Authenticated API requests enabled.")

if not settings.gemini_api_key:
    logger.warning(
        "GEMINI_API_KEY is not set. LLM skill extraction and skill gap generation will be skipped."
    )
else:
    logger.info("Gemini API key detected. LLM features enabled.")

if not settings.nvidia_api_key:
    logger.warning(
        "NVIDIA_API_KEY is not set. LLM summarization for contributing.md file will be skipped."
    )
else:
    logger.info("NVIDIA API key detected. LLM features enabled.")