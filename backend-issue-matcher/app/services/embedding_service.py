from sentence_transformers import SentenceTransformer
from typing import List

# Load the model once
# We use all-MiniLM-L6-v2 as requested for semantic embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

def create_embedding(text: str) -> List[float]:
    """
    Creates a single dense vector embedding for a given text.
    """
    if not text:
        return [0.0] * 384 # 384 is the dimension for all-MiniLM-L6-v2
        
    embedding = model.encode(text)
    return embedding.tolist()

def create_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Creates dense vector embeddings for a list of texts.
    """
    if not texts:
        return []
    
    embeddings = model.encode(texts)
    return embeddings.tolist()
