from fastapi import APIRouter, UploadFile, File
import shutil
import os

from app.services.ocr_service import (
    extract_text_from_image,
    extract_text_from_pdf
)

router = APIRouter()

UPLOAD_DIR = "app/uploads"
ALLOWED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".pdf"]

@router.post("/extract")

async def extract_text(file: UploadFile = File(...)):

    file_path = f"{UPLOAD_DIR}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        return {"error": "Unsupported format"}

    try:
        if extension in [".png", ".jpg", ".jpeg"]:
            text = extract_text_from_image(file_path)
        elif extension == ".pdf":
            text = extract_text_from_pdf(file_path)

        return {
            "filename": file.filename,
            "extracted_text": text
        }
    
    except Exception as e:
        return {"error": str(e)}

