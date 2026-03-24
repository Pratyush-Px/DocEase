from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

# Load the model once
# We use all-MiniLM-L6-v2 as requested for semantic embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

def create_embedding(text: str, prefix: str = "") -> List[float]:
    """
    Creates a single dense vector embedding for a given text.
    Output is always L2-normalized to unit length.
    """
    if not text:
        return [0.0] * 384  # 384 is the dimension for all-MiniLM-L6-v2
        
    embedding = model.encode(prefix + text)
    embedding = embedding / np.linalg.norm(embedding)  # force unit norm
    return embedding.tolist()

def create_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Creates dense vector embeddings for a list of texts.
    Each output vector is L2-normalized to unit length.
    """
    if not texts:
        return []
    
    embeddings = model.encode(texts)
    # Normalize each vector to unit length
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)  # avoid division by zero
    embeddings = embeddings / norms
    return embeddings.tolist()
