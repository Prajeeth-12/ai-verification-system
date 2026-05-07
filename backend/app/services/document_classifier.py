"""
Enterprise Document Classification Engine.

Detects document type from OCR text using pattern matching and keyword analysis.
Used to route to specialized extraction pipelines.

Supported Documents:
    - Aadhaar (Indian ID)
    - Resume/CV
    - PAN (Tax ID)
    - Certificate
    - Experience Letter
    - Passport
    - Driving License
"""

from enum import Enum
from typing import Dict, Tuple
import re

class DocumentType(str, Enum):
    """Supported document types"""
    AADHAAR = "aadhaar"
    RESUME = "resume"
    PAN = "pan"
    CERTIFICATE = "certificate"
    EXPERIENCE_LETTER = "experience_letter"
    PASSPORT = "passport"
    DRIVING_LICENSE = "driving_license"
    UNKNOWN = "unknown"

class DocumentClassifier:
    """
    Intelligent document classifier using pattern matching and keyword analysis.
    
    Classification confidence increases with:
    - Number of document-specific keywords found
    - Presence of unique identifiers
    - Structural patterns
    """
    
    # Document-specific keyword patterns (case-insensitive)
    PATTERNS = {
        DocumentType.AADHAAR: {
            "keywords": [
                r"aadhaar",
                r"uid",
                r"unique identification",
                r"resident of india",
                r"dob|date of birth",
                r"address",
            ],
            "confidence_weight": 1.0
        },
        DocumentType.PAN: {
            "keywords": [
                r"pan",
                r"permanent account number",
                r"income tax",
                r"father's name|father name",
                r"date of birth",
            ],
            "confidence_weight": 0.95
        },
        DocumentType.RESUME: {
            "keywords": [
                r"resume|cv|curriculum vitae",
                r"experience",
                r"education",
                r"skills",
                r"employment|worked",
                r"qualification|degree|bachelor|master",
            ],
            "confidence_weight": 0.9
        },
        DocumentType.CERTIFICATE: {
            "keywords": [
                r"certificate",
                r"certified",
                r"issued|issued to",
                r"date of issue",
                r"valid|validity",
                r"authorized|signature",
            ],
            "confidence_weight": 0.85
        },
        DocumentType.EXPERIENCE_LETTER: {
            "keywords": [
                r"experience letter|experience certificate",
                r"employment confirmation",
                r"worked|employed",
                r"designation|position",
                r"duration|period",
                r"relieving",
            ],
            "confidence_weight": 0.88
        },
        DocumentType.PASSPORT: {
            "keywords": [
                r"passport",
                r"passport number",
                r"country|nationality",
                r"validity|valid till",
                r"issue date|issued",
                r"place of issue",
            ],
            "confidence_weight": 0.92
        },
        DocumentType.DRIVING_LICENSE: {
            "keywords": [
                r"driving license|driving licence",
                r"license number|licence number",
                r"valid till|expiry",
                r"class of vehicle",
                r"dob|date of birth",
            ],
            "confidence_weight": 0.9
        },
    }
    
    @classmethod
    def classify(cls, ocr_text: str) -> Tuple[DocumentType, float, Dict]:
        """
        Classify document type from OCR text.
        
        Args:
            ocr_text: Extracted OCR text from document
        
        Returns:
            Tuple of (document_type, confidence_score, analysis_metadata)
            
        Confidence score: 0.0 - 1.0
            - 0.9+ : Very confident
            - 0.7-0.9 : Confident
            - 0.5-0.7 : Moderate confidence
            - <0.5 : Low confidence (unknown)
        """
        
        text_lower = ocr_text.lower()
        scores: Dict[DocumentType, float] = {}
        keyword_matches: Dict[DocumentType, list] = {}
        
        # Calculate scores for each document type
        for doc_type, pattern_info in cls.PATTERNS.items():
            if doc_type == DocumentType.UNKNOWN:
                continue
            
            keywords = pattern_info["keywords"]
            confidence_weight = pattern_info["confidence_weight"]
            
            # Count keyword matches
            matches = []
            for keyword_pattern in keywords:
                if re.search(keyword_pattern, text_lower):
                    matches.append(keyword_pattern)
            
            # Calculate confidence
            if matches:
                # Confidence = (matches / total_keywords) * weight
                confidence = (len(matches) / len(keywords)) * confidence_weight
                scores[doc_type] = confidence
                keyword_matches[doc_type] = matches
        
        # Find best match
        if not scores:
            return DocumentType.UNKNOWN, 0.0, {
                "reason": "No document patterns matched",
                "text_length": len(ocr_text)
            }
        
        best_doc_type = max(scores, key=scores.get)
        best_score = scores[best_doc_type]
        
        # Return with analysis metadata
        metadata = {
            "confidence": round(best_score, 3),
            "keyword_matches": len(keyword_matches.get(best_doc_type, [])),
            "all_scores": {doc_type.value: round(score, 3) for doc_type, score in scores.items()},
            "matched_keywords": keyword_matches.get(best_doc_type, [])[:3],  # Top 3
            "text_length": len(ocr_text),
            "text_preview": ocr_text[:200]
        }
        
        return best_doc_type, best_score, metadata
    
    @classmethod
    def classify_batch(cls, documents: list) -> list:
        """Classify multiple documents"""
        return [
            {
                "index": idx,
                "type": doc_type.value,
                "confidence": confidence,
                "metadata": metadata
            }
            for idx, doc in enumerate(documents)
            for doc_type, confidence, metadata in [cls.classify(doc)]
        ]
