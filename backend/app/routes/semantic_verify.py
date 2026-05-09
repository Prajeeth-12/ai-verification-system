from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.services.semantic_verification_service import semantic_verification_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/semantic-verify")
async def semantic_verify(parsed_documents: List[Dict[str, Any]]):
    """
    Performs semantic consistency verification across multiple parsed documents.
    Accepts a list of parsed document results.
    """
    if not parsed_documents:
        raise HTTPException(status_code=400, detail="No parsed documents provided")
        
    try:
        logger.info(f"Route: Semantic verification request for {len(parsed_documents)} documents")
        report = semantic_verification_service.verify_semantic_consistency(parsed_documents)
        return report
    except Exception as e:
        logger.error(f"Semantic verification route failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal semantic verification error: {str(e)}")
