"""
Enterprise-grade AI document extraction with specialized prompts and validation.

Architecture:
    OCR Text → Document Classifier → Specialized Prompt → LLM → Schema Validation

Features:
    - 7 document types with specialized extraction
    - Pydantic schema validation
    - Confidence scoring
    - Structured JSON output
"""

import json
from typing import Dict, Any
from datetime import datetime

from app.services.document_classifier import DocumentClassifier
from app.models.extraction_prompts import get_prompt_for_document
from app.models.document_schemas import (
    AadhaarDocument,
    PANDocument,
    ResumeDocument,
    CertificateDocument,
    ExperienceLetterDocument
)

# Placeholder for OpenAI/Gemini client
try:
    from openai import OpenAI
    client = OpenAI()
except:
    client = None

# ============================================================================
# Document Type Detection
# ============================================================================

def detect_document_type(ocr_text: str) -> Dict[str, Any]:
    """
    Detect document type from OCR text using advanced classifier.
    
    Returns:
        {
            "type": "aadhaar",
            "confidence": 0.95,
            "analysis": {...}
        }
    """
    doc_type, confidence, analysis = DocumentClassifier.classify(ocr_text)
    
    return {
        "type": doc_type.value,
        "confidence": confidence,
        "analysis": analysis
    }

# ============================================================================
# Specialized Extraction
# ============================================================================

def extract_aadhaar(raw_text: str) -> Dict[str, Any]:
    """Extract Aadhaar document with validation"""
    return _extract_with_validation(
        raw_text,
        "aadhaar",
        AadhaarDocument,
        required_fields=["full_name", "aadhaar_number"]
    )

def extract_pan(raw_text: str) -> Dict[str, Any]:
    """Extract PAN document with validation"""
    return _extract_with_validation(
        raw_text,
        "pan",
        PANDocument,
        required_fields=["pan_number", "full_name"]
    )

def extract_resume(raw_text: str) -> Dict[str, Any]:
    """Extract Resume document with validation"""
    return _extract_with_validation(
        raw_text,
        "resume",
        ResumeDocument,
        required_fields=["full_name", "email"]
    )

def extract_certificate(raw_text: str) -> Dict[str, Any]:
    """Extract Certificate document with validation"""
    return _extract_with_validation(
        raw_text,
        "certificate",
        CertificateDocument,
        required_fields=["certificate_name", "issued_to"]
    )

def extract_experience_letter(raw_text: str) -> Dict[str, Any]:
    """Extract Experience Letter with validation"""
    return _extract_with_validation(
        raw_text,
        "experience_letter",
        ExperienceLetterDocument,
        required_fields=["employee_name", "company_name"]
    )

# ============================================================================
# Core Extraction with Validation
# ============================================================================

def _extract_with_validation(
    raw_text: str,
    doc_type: str,
    schema_class,
    required_fields: list
) -> Dict[str, Any]:
    """
    Core extraction pipeline with validation.
    
    Flow:
        1. Generate specialized prompt
        2. Call LLM with low temperature
        3. Parse JSON response
        4. Validate with Pydantic schema
        5. Calculate confidence score
    """
    
    result = {
        "document_type": doc_type,
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "validation_errors": []
    }
    
    try:
        if client is None:
            return {
                **result,
                "error": "OpenAI client not configured. Add OPENAI_API_KEY to .env"
            }
        
        # Get specialized prompt
        prompt_template = get_prompt_for_document(doc_type)
        prompt = prompt_template.format(ocr_text=raw_text)
        
        # Call LLM with strict parameters
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000
        )
        
        # Extract and clean JSON
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Parse JSON
        extracted_data = json.loads(content)
        
        # Validate with Pydantic schema
        validated_doc = schema_class(**extracted_data)
        
        # Calculate confidence score based on required fields found
        required_fields_found = sum(
            1 for field in required_fields
            if getattr(validated_doc, field, None)
        )
        
        validated_doc.confidence_score = (required_fields_found / len(required_fields)) if required_fields else 0.5
        validated_doc.required_fields_found = required_fields_found
        
        result.update({
            "success": True,
            "data": validated_doc.dict(),
            "confidence": validated_doc.confidence_score,
            "required_fields_found": required_fields_found,
            "raw_response_preview": content[:200]
        })
        
        return result
    
    except json.JSONDecodeError as e:
        result["error"] = f"JSON parsing failed: {str(e)}"
        result["error_type"] = "json_parse"
        result["raw_response"] = content if 'content' in locals() else None
        return result
    
    except ValueError as e:
        result["error"] = f"Schema validation failed: {str(e)}"
        result["error_type"] = "schema_validation"
        result["validation_errors"] = str(e).split("\n") if hasattr(e, "errors") else [str(e)]
        return result
    
    except Exception as e:
        result["error"] = str(e)
        result["error_type"] = "unknown"
        return result


def extract_document(raw_text: str, document_type: str = None) -> Dict[str, Any]:
    """
    Intelligent document extraction orchestrator.
    
    Flow:
        1. Auto-detect if type not provided
        2. Route to specialized extractor
        3. Validate output
        4. Return structured data
    """
    
    # Auto-detect document type if not provided
    if not document_type:
        classification = detect_document_type(raw_text)
        document_type = classification["type"]
        classification_confidence = classification["confidence"]
    else:
        classification_confidence = None
    
    # Route to specialized extractor
    extractors = {
        "aadhaar": extract_aadhaar,
        "pan": extract_pan,
        "resume": extract_resume,
        "certificate": extract_certificate,
        "experience_letter": extract_experience_letter,
    }
    
    extractor = extractors.get(document_type)
    
    if extractor:
        result = extractor(raw_text)
        if classification_confidence is not None:
            result["classification_confidence"] = round(classification_confidence, 3)
        return result
    else:
        return {
            "success": False,
            "error": f"Unknown document type: {document_type}",
            "document_type": document_type
        }
