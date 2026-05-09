from fastapi import APIRouter, HTTPException
from app.services.document_classifier import classify_document

router = APIRouter()

@router.post("/classify")
async def classify(text: str):
    """
    Classify a document type based on its OCR text.
    """
    if not text:
        raise HTTPException(status_code=400, detail="Text is required for classification")
    
    try:
        doc_type, confidence = classify_document(text)
        return {
            "document_type": doc_type,
            "confidence": f"{confidence:.2f}%"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
