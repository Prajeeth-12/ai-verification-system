from fastapi import APIRouter, HTTPException
from app.services.semantic_service import validate_claims
from typing import List

router = APIRouter()

@router.post("/validate-claims")
async def validate(skills: List[str], certificates: List[str]):
    """
    Semantically validate skills against uploaded certificates.
    """
    try:
        results = validate_claims(skills, certificates)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
