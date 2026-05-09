import logging
import time
from typing import List, Union, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from functools import lru_cache

# Configure structured logging
logger = logging.getLogger(__name__)

class EmbeddingService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def _get_model(self):
        """Lazy-loaded singleton model initialization"""
        if self._model is None:
            logger.info("EMBEDDING_MODEL_LOADING: Initializing all-MiniLM-L6-v2")
            start_time = time.time()
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            loading_time = time.time() - start_time
            logger.info(f"EMBEDDING_MODEL_LOADED: Time={loading_time:.2f}s, Dimensions=384")
        return self._model

    @lru_cache(maxsize=1024)
    def generate_embedding(self, text: str) -> List[float]:
        """Generates embedding for a single text string with caching"""
        if not text:
            return []
        
        model = self._get_model()
        start_time = time.time()
        
        embedding = model.encode(text, convert_to_numpy=True)
        
        generation_time = time.time() - start_time
        logger.debug(f"EMBEDDING_GENERATED: TextLength={len(text)}, Time={generation_time:.4f}s")
        
        return embedding.tolist()

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of texts"""
        if not texts:
            return []
            
        model = self._get_model()
        start_time = time.time()
        
        embeddings = model.encode(texts, convert_to_numpy=True)
        
        generation_time = time.time() - start_time
        logger.info(f"BATCH_EMBEDDINGS_GENERATED: Count={len(texts)}, Time={generation_time:.4f}s, AvgTime={generation_time/len(texts):.4f}s")
        
        return embeddings.tolist()

# Global instance for easy access
embedding_service = EmbeddingService()

def generate_embedding(text: str) -> List[float]:
    return embedding_service.generate_embedding(text)

def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    return embedding_service.generate_embeddings_batch(texts)
