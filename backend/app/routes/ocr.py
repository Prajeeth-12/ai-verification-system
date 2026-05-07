"""
OCR extraction route with hybrid NVIDIA + EasyOCR pipeline.

Endpoints:
    POST /extract - Extract text from uploaded documents
"""

from fastapi import APIRouter, UploadFile, File
import shutil
import os

from app.services.ocr_service import extract_text

router = APIRouter()

UPLOAD_DIR = "app/uploads"
ALLOWED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".pdf"]

@router.post("/extract")
async def extract_text_endpoint(file: UploadFile = File(...)):
    """
    Extract text from uploaded document using hybrid OCR pipeline.
    
    Supports:
        - PDF files
        - PNG images
        - JPG/JPEG images
    
    OCR Flow:
        1. Upload file
        2. Try NVIDIA NIM OCR (primary)
        3. Fallback to EasyOCR if NVIDIA fails
        4. Return extracted text + provider metadata
    
    Response includes:
        - filename: original filename
        - extracted_text: OCR result
        - ocr_provider: which engine processed (nvidia or easyocr)
        - extraction_time_ms: processing time
        - success: whether extraction succeeded
    """
    
    file_path = f"{UPLOAD_DIR}/{file.filename}"
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate file extension
        extension = os.path.splitext(file.filename)[1].lower()
        
        if extension not in ALLOWED_EXTENSIONS:
            return {
                "success": False,
                "error": f"Unsupported format: {extension}",
                "allowed_formats": ALLOWED_EXTENSIONS,
                "filename": file.filename
            }
        
        # Extract text using hybrid pipeline
        extracted_text, metadata = extract_text(file_path)
        
        # Return response with provider info
        return {
            "success": metadata.get("success", False),
            "filename": file.filename,
            "extracted_text": extracted_text,
            "ocr_provider": metadata.get("provider"),
            "extraction_time_ms": metadata.get("extraction_time_ms"),
            "document_type": metadata.get("document_type"),
            "pages_processed": metadata.get("pages_processed"),
            "providers_used": metadata.get("providers_used"),
            "fallback_used": metadata.get("fallback_reason") is not None,
            "metadata": metadata
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "filename": file.filename
        }
    
    finally:
        # Cleanup uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

