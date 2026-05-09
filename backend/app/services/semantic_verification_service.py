import logging
import time
from typing import List, Dict, Any, Optional
from app.services.embedding_service import generate_embedding, generate_embeddings_batch
from app.services.vector_service import vector_service
import numpy as np

# Configure structured logging
logger = logging.getLogger(__name__)

# Thresholds for semantic matching
THRESHOLD_STRONG = 0.85
THRESHOLD_WEAK = 0.65

class SemanticVerificationService:
    def verify_semantic_consistency(self, parsed_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Performs RAG-style semantic consistency analysis across all parsed documents.
        Checks if claims in one document (e.g., Resume) are supported by others (e.g., Certificates, IDs).
        """
        logger.info(f"SEMANTIC_VERIFICATION_START: Processing {len(parsed_documents)} documents")
        start_time = time.time()

        # 1. Index all documents for retrieval
        self._index_all_claims(parsed_documents)

        matched_claims = []
        unverified_claims = []
        risk_flags = []
        similarity_scores = {}
        
        # 2. Analyze Document Claims
        for doc in parsed_documents:
            doc_type = doc.get("metadata", {}).get("document_type", "unknown").lower()
            data = doc.get("data", {})
            
            if doc_type == "resume":
                self._verify_resume_claims(data, matched_claims, unverified_claims, risk_flags, similarity_scores)
            elif doc_type == "certificate":
                self._verify_certificate_validity(data, matched_claims, unverified_claims, risk_flags, similarity_scores)

        # 3. Calculate Weighted Semantic Score
        total_claims = len(matched_claims) + len(unverified_claims)
        semantic_score = 100
        if total_claims > 0:
            match_ratio = len(matched_claims) / total_claims
            semantic_score = int(match_ratio * 100)
            
            # Deduct for specific risks
            semantic_score -= (len(risk_flags) * 15)
            semantic_score = max(0, min(100, semantic_score))

        report = {
            "semantic_score": semantic_score,
            "matched_claims": matched_claims,
            "unverified_claims": unverified_claims,
            "risk_flags": risk_flags,
            "similarity_scores": similarity_scores,
            "metadata": {
                "total_claims_analyzed": total_claims,
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        }

        logger.info(f"SEMANTIC_VERIFICATION_COMPLETE: Score={semantic_score}, Matches={len(matched_claims)}, Risks={len(risk_flags)}")
        return report

    def _index_all_claims(self, documents: List[Dict[str, Any]]):
        """Pre-indexes all document fields into the vector service for RAG-style lookup"""
        vector_service.create_index() # Clear for current session analysis
        
        all_embeddings = []
        all_metadata = []
        
        for doc in documents:
            doc_type = doc.get("metadata", {}).get("document_type", "unknown")
            data = doc.get("data", {})
            
            for field, value in data.items():
                if isinstance(value, str) and len(value) > 3:
                    all_embeddings.append(generate_embedding(value))
                    all_metadata.append({
                        "doc_type": doc_type,
                        "field": field,
                        "value": value
                    })
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            all_embeddings.append(generate_embedding(item))
                            all_metadata.append({
                                "doc_type": doc_type,
                                "field": f"{field}_item",
                                "value": item
                            })

        if all_embeddings:
            vector_service.add_embeddings(all_embeddings, all_metadata)

    def _verify_resume_claims(self, resume_data: Dict[str, Any], matched: List[str], unverified: List[str], flags: List[str], scores: Dict[str, float]):
        """Verifies skills and education claims from resume against other documents"""
        
        # Verify Skills
        skills = resume_data.get("skills", [])
        if isinstance(skills, list):
            for skill in skills:
                results = vector_service.search_similar(generate_embedding(skill), top_k=3)
                best_match = self._find_best_cross_doc_match(skill, results, exclude_type="resume")
                
                if best_match and best_match["score"] >= THRESHOLD_WEAK:
                    matched.append(f"Skill: {skill} supported by {best_match['metadata']['doc_type']}")
                    scores[skill] = best_match["score"]
                    logger.info(f"SEMANTIC_MATCH: Skill '{skill}' matched with '{best_match['metadata']['value']}' ({best_match['score']:.2f})")
                else:
                    unverified.append(f"Skill: {skill}")
                    if skill not in scores: scores[skill] = 0.0

        # Verify Education
        education = resume_data.get("education", [])
        if education:
            edu_str = str(education)
            results = vector_service.search_similar(generate_embedding(edu_str), top_k=3)
            best_match = self._find_best_cross_doc_match(edu_str, results, exclude_type="resume")
            
            if best_match and best_match["score"] >= THRESHOLD_STRONG:
                matched.append(f"Education claim verified by {best_match['metadata']['doc_type']}")
            else:
                unverified.append("Education details")
                flags.append("UNVERIFIED_EDUCATION: No supporting certificates found for education claims")

    def _verify_certificate_validity(self, cert_data: Dict[str, Any], matched: List[str], unverified: List[str], flags: List[str], scores: Dict[str, float]):
        """Ensures certificate belongs to the applicant and is consistent with profile"""
        cert_name = cert_data.get("name", "")
        if cert_name:
            # Search for this name in IDs/Resume
            results = vector_service.search_similar(generate_embedding(cert_name), top_k=3)
            best_match = self._find_best_cross_doc_match(cert_name, results, exclude_type="certificate")
            
            if not best_match or best_match["score"] < THRESHOLD_STRONG:
                flags.append(f"CERTIFICATE_OWNERSHIP_DOUBT: Certificate '{cert_data.get('certificate_type')}' name mismatch")
                logger.warning(f"SEMANTIC_MISMATCH: Certificate owner '{cert_name}' not strongly matched in other docs")

    def _find_best_cross_doc_match(self, query: str, results: List[Dict[str, Any]], exclude_type: str) -> Optional[Dict[str, Any]]:
        """Filters search results to find matches in OTHER documents"""
        cross_doc_matches = [r for r in results if r["metadata"]["doc_type"].lower() != exclude_type.lower()]
        if cross_doc_matches:
            return max(cross_doc_matches, key=lambda x: x["score"])
        return None

# Global instance
semantic_verification_service = SemanticVerificationService()
