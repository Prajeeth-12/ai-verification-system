from fastapi import APIRouter, HTTPException
from app.services.verification_service import verify_documents
from typing import List, Dict, Any

router = APIRouter()

@router.post("/verify")
async def verify(documents: List[Dict[str, Any]]):
    """
    Verify multiple parsed documents for consistency.
    """
    if not documents:
        raise HTTPException(status_code=400, detail="At least one document is required")
    
    try:
        result = verify_documents(documents)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
