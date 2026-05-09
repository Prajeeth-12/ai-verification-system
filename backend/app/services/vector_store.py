import faiss
import numpy as np
import os
import pickle
from typing import List, Dict, Any
from app.services.embedding_service import generate_embeddings

class VectorStore:
    def __init__(self, index_path: str = "faiss_index"):
        self.index_path = index_path
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = [] # Stores actual text chunks and source info
        
        # Load existing index if it exists
        if os.path.exists(index_path):
            self.load()

    def add_documents(self, chunks: List[str], source_id: str):
        """
        Embeds chunks and adds them to the FAISS index with metadata.
        """
        if not chunks:
            return
            
        embeddings = generate_embeddings(chunks)
        
        # Add to FAISS
        self.index.add(np.array(embeddings).astype('float32'))
        
        # Update metadata
        for chunk in chunks:
            self.metadata.append({
                "text": chunk,
                "source": source_id
            })
        
        # Auto-save after addition
        self.save()

    def search_similar(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves the most relevant chunks for a given query.
        """
        query_embedding = generate_embeddings([query])
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), top_k)
        
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx != -1 and idx < len(self.metadata):
                results.append({
                    "content": self.metadata[idx]["text"],
                    "source": self.metadata[idx]["source"],
                    "score": float(distances[0][i])
                })
        return results

    def save(self):
        """Persists the FAISS index and metadata to disk"""
        if not os.path.exists(self.index_path):
            os.makedirs(self.index_path)
            
        faiss.write_index(self.index, os.path.join(self.index_path, "index.faiss"))
        with open(os.path.join(self.index_path, "metadata.pkl"), "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self):
        """Loads the FAISS index and metadata from disk"""
        index_file = os.path.join(self.index_path, "index.faiss")
        meta_file = os.path.join(self.index_path, "metadata.pkl")
        
        if os.path.exists(index_file) and os.path.exists(meta_file):
            self.index = faiss.read_index(index_file)
            with open(meta_file, "rb") as f:
                self.metadata = pickle.load(f)

# Global instance for easy access
vector_store = VectorStore()
