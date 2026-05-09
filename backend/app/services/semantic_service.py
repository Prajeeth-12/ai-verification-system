from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Load a lightweight model
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

class SemanticSearch:
    def __init__(self):
        self.model = get_model()
        self.index = None
        self.documents = []

    def add_documents(self, docs):
        """Adds documents to the FAISS index"""
        self.documents = docs
        embeddings = self.model.encode(docs)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))

    def search(self, query, top_k=3):
        """Searches for similar documents"""
        if self.index is None:
            return []
            
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), top_k)
        
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx != -1:
                results.append({
                    "document": self.documents[idx],
                    "score": float(distances[0][i])
                })
        return results

def validate_claims(resume_skills, certificates):
    """
    Performs embedding-based semantic verification using FAISS vector search 
    to detect unsupported claims and inconsistencies.
    """
    if not resume_skills or not certificates:
        return []
        
    searcher = SemanticSearch()
    searcher.add_documents(certificates)
    
    findings = []
    for skill in resume_skills:
        results = searcher.search(skill, top_k=1)
        # Low distance means high similarity
        if results and results[0]["score"] < 0.8:
            findings.append({"skill": skill, "status": "Supported", "matched_with": results[0]["document"]})
        else:
            findings.append({"skill": skill, "status": "Potential unsupported claim"})
            
    return findings
