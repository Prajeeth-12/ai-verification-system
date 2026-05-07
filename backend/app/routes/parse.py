from fastapi import APIRouter, UploadFile, File
import json
from datetime import datetime
import os

from app.services.ai_service import extract_document, detect_document_type

router = APIRouter()

DEBUG_DIR = "app/debug"

def log_extraction(document_type, ocr_text, extraction_result, status="success"):
    """Log OCR and extraction results for debugging"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{DEBUG_DIR}/{document_type}_{timestamp}.json"
    
    log_data = {
        "timestamp": timestamp,
        "document_type": document_type,
        "status": status,
        "ocr_text_preview": ocr_text[:300] if ocr_text else None,
        "extraction": extraction_result
    }
    
    try:
        with open(log_file, "w") as f:
            json.dump(log_data, f, indent=2)
    except Exception as e:
        print(f"Logging error: {str(e)}")

@router.post("/parse")
async def parse_document(ocr_text: str, document_type: str = None):
    """
    Parse OCR extracted text using AI structured extraction.
    
    Auto-classifies document if type not provided.
    Returns ONLY raw JSON - no markdown, no explanations.
    """
    try:
        # Auto-classify if not provided
        if not document_type:
            classification = detect_document_type(ocr_text)
            document_type = classification["type"]
        
        # Extract structured data
        result = extract_document(ocr_text, document_type)
        
        # Log the extraction
        log_extraction(document_type, ocr_text, result, "success")
        
        return result
    
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "document_type": document_type
        }
        log_extraction(document_type or "unknown", ocr_text, error_result, "failed")
        return error_result

