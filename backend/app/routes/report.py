from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.services.report_service import generate_and_upload_report
from app.config import settings
import os

router = APIRouter()

@router.post("/generate-report")
async def create_report(report_data: dict):
    """
    Generate a PDF report for the given verification data.
    """
    report_filename = f"report_{os.urandom(4).hex()}.pdf"
    output_path = os.path.join(settings.UPLOAD_DIR, report_filename)
    
    try:
        generate_pdf_report(report_data, output_path)
        return {
            "message": "Report generated successfully",
            "report_url": f"/download/{report_filename}",
            "filename": report_filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
async def download_report(filename: str):
    """
    Download a generated report.
    """
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)
