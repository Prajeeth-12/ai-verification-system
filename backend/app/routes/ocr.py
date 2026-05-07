from fastapi import APIRouter, HTTPException
from app.services.ocr_service import process_file
from app.config import settings
import os

router = APIRouter()

@router.post("/extract")
async def extract_text(filename: str):
    """
    Extract text from a previously uploaded file.
    """
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        text, metadata = process_file(file_path)
        return {
            "filename": filename,
            "text": text,
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
