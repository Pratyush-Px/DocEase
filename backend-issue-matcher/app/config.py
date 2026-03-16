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
    faiss_index_dir: str = "data/faiss_index"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Ensure FAISS index directory exists
os.makedirs(settings.faiss_index_dir, exist_ok=True)
