from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from app.services.agent_service import run_full_orchestration
from app.services.database_service import get_document_by_filename
from app.services.report_service import generate_and_upload_report
from typing import List, Optional, Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ProcessRequest(BaseModel):
    filenames: Optional[List[str]] = None
    urls: Optional[List[str]] = None
    file_id: Optional[str] = None
    filename: Optional[str] = None

@router.post("/process-complete")
async def process_complete(
    request: ProcessRequest = Body(...)
) -> Dict[str, Any]:
    """
    Executes the full multi-agent LangGraph orchestration, 
    generates a PDF report, and returns the final verification verdict.
    """
    target_urls = request.urls or []
    filenames = request.filenames or []
    
    # Handle single filename from frontend if provided
    if request.filename and request.filename not in filenames:
        filenames.append(request.filename)
    
    # Resolve filenames to URLs
    if filenames:
        for name in filenames:
            doc = get_document_by_filename(name)
            if not doc:
                # Silently log if not found or raise if critical
                logger.warning(f"Document '{name}' not found in database")
                continue
            
            file_url = doc.get("file_url")
            if file_url and file_url not in target_urls:
                target_urls.append(file_url)
            
    if not target_urls:
        logger.error(f"PROCESS_COMPLETE_ERROR: No URLs found for filenames {filenames}")
        raise HTTPException(status_code=400, detail="No URLs or filenames provided")
        
    try:
        logger.info(f"WORKFLOW_START: Full orchestration for {len(target_urls)} documents")
        
        # 1. Run Multi-Agent Orchestration
        workflow_state = await run_full_orchestration(target_urls)
        
        if workflow_state.get("status") == "failed":
            raise HTTPException(status_code=500, detail={"errors": workflow_state.get("errors")})
            
        # 2. Generate and Upload Report
        report_url = generate_and_upload_report(workflow_state)
        
        # 3. Format Response
        final_report = workflow_state.get("final_report", {})
        
        # Extract report filename from URL if possible
        report_filename = report_url.split("/")[-1] if report_url else "report.pdf"
        
        return {
            "verification_score": final_report.get("verification_details", {}).get("verification_score"),
            "semantic_score": final_report.get("semantic_details", {}).get("semantic_score"),
            "overall_score": final_report.get("overall_score"),
            "risk_level": final_report.get("risk_level"),
            "report_url": report_url,
            "report_filename": report_filename,
            "flags": final_report.get("flags", []),
            "status": workflow_state.get("status"),
            "document_summaries": workflow_state.get("parsed_docs", [])
        }
        
    except Exception as e:
        logger.error(f"PROCESS_COMPLETE_FAILED: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
