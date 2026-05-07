from fastapi import APIRouter, UploadFile, File
import shutil

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    
    file_location = f"app/uploads/{file.filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": file.filename,
        "message": "File uploaded successfully"
    }
