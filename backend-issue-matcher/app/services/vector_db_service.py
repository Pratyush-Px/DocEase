import os
import json
import faiss
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from app.config import settings, logger

# We use an L2 distance index
# Since embeddings from all-MiniLM-L6-v2 are 384 dimensions
DIMENSION = 384

def get_repo_identifier(repo_url: str) -> str:
    """
    Returns a safe string identifier for a repository (e.g., 'huggingface_transformers')
    """
    repo_path = repo_url.replace("https://github.com/", "").strip("/")
    return repo_path.replace("/", "_")

def get_index_paths(repo_identifier: str) -> Tuple[str, str]:
    """
    Returns the paths to the FAISS index and metadata JSON files.
    """
    index_path = os.path.join(settings.faiss_index_dir, f"{repo_identifier}.index")
    metadata_path = os.path.join(settings.faiss_index_dir, f"{repo_identifier}_metadata.json")
    return index_path, metadata_path

def is_index_fresh(index_path: str, max_age_hours: int = 24) -> bool:
    """
    Checks if the index file is younger than the specified age limit.
    """
    if not os.path.exists(index_path):
        return False
        
    mod_time = datetime.fromtimestamp(os.path.getmtime(index_path))
    age = datetime.now() - mod_time
    
    return age < timedelta(hours=max_age_hours)

def create_and_save_index(repo_identifier: str, embeddings: List[List[float]], metadata: List[Dict[str, Any]]):
    """
    Creates a FAISS index from embeddings, saves it, and saves metadata.
    """
    if not embeddings:
        logger.warning(f"No embeddings to index for {repo_identifier}")
        return
        
    # Create the FAISS index
    index = faiss.IndexFlatL2(DIMENSION)
    
    # Add embeddings (convert to numpy array first)
    embeddings_np = np.array(embeddings).astype('float32')
    index.add(embeddings_np)
    
    # Save the index to disk
    index_path, metadata_path = get_index_paths(repo_identifier)
    faiss.write_index(index, index_path)
    logger.info(f"Saved FAISS index to {index_path}")
    
    # Save metadata to disk
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")

def load_index_and_metadata(repo_identifier: str) -> Tuple[Any, List[Dict[str, Any]]]:
    """
    Loads an existing FAISS index and its corresponding metadata.
    Returns (None, None) if they don't exist.
    """
    index_path, metadata_path = get_index_paths(repo_identifier)
    
    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        return None, None
        
    try:
        index = faiss.read_index(index_path)
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return index, metadata
    except Exception as e:
        logger.error(f"Failed to load index or metadata for {repo_identifier}: {e}")
        return None, None

def search_index(index, query_embedding: List[float], k: int = 20) -> Tuple[List[float], List[int]]:
    """
    Searches the FAISS index for the k nearest neighbors.
    Returns distances and indices.
    """
    # FAISS requires a 2D numpy array
    query_np = np.array([query_embedding]).astype('float32')
    
    # Perform the search
    distances, indices = index.search(query_np, k)
    
    # Flatten the results
    return distances[0].tolist(), indices[0].tolist()
