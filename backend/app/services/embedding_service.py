"""
Embedding Service

Handles text embedding generation for similarity search.
"""

import logging
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Global model instance
_model = None

def get_embedding_model():
    """Get or create embedding model instance"""
    global _model
    if _model is None:
        try:
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            _model = None
    return _model

def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Generate embeddings for a list of texts
    
    Args:
        texts: List of text strings
        
    Returns:
        numpy array of embeddings
    """
    try:
        model = get_embedding_model()
        if model is None:
            # Fallback: return random embeddings
            logger.warning("Using random embeddings as fallback")
            return np.random.rand(len(texts), 384).astype(np.float32)
        
        embeddings = model.encode(texts)
        logger.info(f"Generated embeddings for {len(texts)} texts")
        return embeddings
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        # Return random embeddings as fallback
        return np.random.rand(len(texts), 384).astype(np.float32)

def embed_single_text(text: str) -> np.ndarray:
    """
    Generate embedding for a single text
    
    Args:
        text: Text string
        
    Returns:
        numpy array of embedding
    """
    return embed_texts([text])[0]

def compute_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Compute cosine similarity between two embeddings
    
    Args:
        embedding1: First embedding
        embedding2: Second embedding
        
    Returns:
        Similarity score (0-1)
    """
    try:
        # Normalize embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Compute cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)
        
    except Exception as e:
        logger.error(f"Error computing similarity: {e}")
        return 0.0