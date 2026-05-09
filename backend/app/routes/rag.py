from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from app.services.embedding_service import chunk_text
from app.services.vector_store import vector_store
from app.services.rag_service import generate_rag_response
from app.services.ocr_service import process_file
import os

router = APIRouter()

class IngestRequest(BaseModel):
    file_path: str
    source_id: Optional[str] = None

class QueryRequest(BaseModel):
    question: str

@router.post("/ingest")
async def ingest_document(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Ingests a document: OCR -> Chunking -> Embedding -> FAISS
    """
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    source_id = request.source_id or os.path.basename(request.file_path)
    
    # Run heavy processing in background
    background_tasks.add_task(process_and_index, request.file_path, source_id)
    
    return {"message": f"Ingestion started for {source_id}", "status": "processing"}

@router.post("/query")
async def query_rag(request: QueryRequest):
    """
    Asks a semantic question using the RAG pipeline.
    """
    response = generate_rag_response(request.question)
    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
    return response

async def process_and_index(file_path: str, source_id: str):
    """Background task for document indexing"""
    try:
        # 1. OCR
        text, metadata = process_file(file_path)
        
        # 2. Chunking
        chunks = chunk_text(text)
        
        # 3. Vector Storage (Embeddings + FAISS)
        vector_store.add_documents(chunks, source_id)
        
        print(f"Successfully indexed {source_id} ({len(chunks)} chunks)")
    except Exception as e:
        print(f"Failed to index {source_id}: {str(e)}")
