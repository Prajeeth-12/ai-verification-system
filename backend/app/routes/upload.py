from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
from app.config import settings

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document for processing.
    Supported formats: PDF, PNG, JPG, JPEG
    """
    # Validate file extension
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Supported types: {', '.join(allowed_extensions)}"
        )

    # Define save path
    save_path = os.path.join(settings.UPLOAD_DIR, file.filename)

    try:
        # Save file to disk
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "filename": file.filename,
            "save_path": save_path,
            "content_type": file.content_type,
            "status": "success",
            "message": "File uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
