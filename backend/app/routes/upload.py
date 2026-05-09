from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import logging
from app.services.storage_service import upload_to_storage
from app.services.database_service import save_uploaded_document
from app.utils.file_utils import sanitize_filename

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document to Supabase Storage and persist metadata to PostgreSQL.
    Supported formats: PDF, PNG, JPG, JPEG
    Filenames are sanitized (lowercase, no spaces, no unsafe chars).
    """
    # 1. Sanitize filename
    original_filename = file.filename
    sanitized_name = sanitize_filename(original_filename)
    logger.info(f"Sanitized filename: '{original_filename}' -> '{sanitized_name}'")

    # 2. Validate file extension
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
    file_ext = os.path.splitext(sanitized_name)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Supported types: {', '.join(allowed_extensions)}"
        )

    try:
        # Read file bytes
        file_bytes = await file.read()
        
        # 3. Upload to Supabase Storage
        logger.info(f"Initiating storage upload for {sanitized_name}")
        storage_result = upload_to_storage(file_bytes, sanitized_name)
        
        # 4. Persist metadata to Supabase PostgreSQL
        logger.info(f"Persisting metadata for {sanitized_name} to database")
        doc_data = {
            "filename": sanitized_name,
            "document_type": "unknown", # Initial classification will happen in OCR pipeline
            "file_url": storage_result["public_url"],
            "verification_status": "pending",
            "confidence_score": 0.0,
            "extracted_data": {}
        }
        
        db_result = save_uploaded_document(doc_data)
        
        return {
            "id": db_result.get("id") if db_result else None,
            "filename": sanitized_name,
            "original_filename": original_filename,
            "url": storage_result["public_url"],
            "status": "success",
            "message": "File uploaded and metadata persisted successfully"
        }
        
    except Exception as e:
        logger.error(f"Upload workflow failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")
