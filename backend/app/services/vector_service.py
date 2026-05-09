import faiss
import numpy as np
import os
import pickle
import logging
import time
from typing import List, Dict, Any, Optional

# Configure structured logging
logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self, index_dir: str = "app/storage/vector_index"):
        self.index_dir = index_dir
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self.index = None
        self.metadata = []  # Stores mapping of index to metadata
        
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
            
        self.load_index()
        if self.index is None:
            self.create_index()

    def create_index(self):
        """Initializes a new FAISS index for Inner Product (Cosine Similarity)"""
        logger.info(f"VECTOR_INDEX_CREATE: Dimension={self.dimension}")
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []

    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """Normalizes vectors for Cosine Similarity using Inner Product"""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / (norms + 1e-10)

    def add_embeddings(self, embeddings: List[List[float]], metadata_list: List[Dict[str, Any]]):
        """Adds embeddings and corresponding metadata to the index"""
        if not embeddings:
            return
            
        start_time = time.time()
        v_arr = np.array(embeddings).astype('float32')
        v_arr = self._normalize_vectors(v_arr)
        
        self.index.add(v_arr)
        self.metadata.extend(metadata_list)
        
        latency = time.time() - start_time
        logger.info(f"VECTOR_INSERTION: Count={len(embeddings)}, Latency={latency:.4f}s, TotalIndexSize={self.index.ntotal}")
        self.save_index()

    def search_similar(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Searches for similar vectors using cosine similarity"""
        if self.index is None or self.index.ntotal == 0:
            return []
            
        start_time = time.time()
        q_arr = np.array([query_embedding]).astype('float32')
        q_arr = self._normalize_vectors(q_arr)
        
        distances, indices = self.index.search(q_arr, top_k)
        
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx != -1 and idx < len(self.metadata):
                results.append({
                    "metadata": self.metadata[idx],
                    "score": float(distances[0][i])
                })
                
        latency = time.time() - start_time
        logger.info(f"VECTOR_SEARCH: TopK={top_k}, Latency={latency:.4f}s, BestScore={results[0]['score'] if results else 'N/A'}")
        return results

    def save_index(self):
        """Persists FAISS index and metadata to disk"""
        try:
            index_path = os.path.join(self.index_dir, "faiss.index")
            meta_path = os.path.join(self.index_dir, "metadata.pkl")
            
            faiss.write_index(self.index, index_path)
            with open(meta_path, "wb") as f:
                pickle.dump(self.metadata, f)
            logger.info("VECTOR_INDEX_SAVED: Local persistence successful")
        except Exception as e:
            logger.error(f"VECTOR_INDEX_SAVE_FAILED: {str(e)}")

    def load_index(self):
        """Loads FAISS index and metadata from disk"""
        try:
            index_path = os.path.join(self.index_dir, "faiss.index")
            meta_path = os.path.join(self.index_dir, "metadata.pkl")
            
            if os.path.exists(index_path) and os.path.exists(meta_path):
                self.index = faiss.read_index(index_path)
                with open(meta_path, "rb") as f:
                    self.metadata = pickle.load(f)
                logger.info(f"VECTOR_INDEX_LOADED: Size={self.index.ntotal}")
            else:
                logger.warning("VECTOR_INDEX_NOT_FOUND: Starting with fresh index")
        except Exception as e:
            logger.error(f"VECTOR_INDEX_LOAD_FAILED: {str(e)}")
            self.create_index()

# Global instance
vector_service = VectorService()
