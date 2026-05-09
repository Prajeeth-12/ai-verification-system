from typing import List, Dict, Any
from app.services.vector_store import vector_store
from app.services.parsing_service import parse_with_ai
import requests
import json
from app.config import settings

def retrieve_context(query: str, top_k: int = 5) -> str:
    """
    Retrieves relevant document chunks and formats them as context for the LLM.
    """
    relevant_chunks = vector_store.search_similar(query, top_k=top_k)
    
    context = "RELEVANT DOCUMENT CONTEXT:\n"
    for i, chunk in enumerate(relevant_chunks):
        context += f"[{i+1}] Source: {chunk['source']}\nContent: {chunk['content']}\n\n"
        
    return context

def generate_rag_response(question: str) -> Dict[str, Any]:
    """
    Retrieves context and generates an augmented response using NVIDIA NIM.
    """
    context = retrieve_context(question)
    
    # Construct the RAG Prompt
    prompt = f"""
    You are an AI Document Verification Expert. Use the provided context to answer the user's question accurately.
    If the answer isn't explicitly in the context, state that you cannot verify it.
    
    {context}
    
    USER QUESTION: {question}
    
    ANSWER (Be concise and professional):
    """
    
    # Reuse NVIDIA NIM logic from parsing_service (could be refactored into a general AI utility)
    url = "https://ai.api.nvidia.com/v1/genai/nvidia/nemotron-3-super-120b-a12b"
    
    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
        "Accept": "application/json"
    }
    
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return {
            "answer": answer,
            "sources": [chunk['source'] for chunk in vector_store.search_similar(question, top_k=2)]
        }
    except Exception as e:
        return {"error": f"RAG Generation failed: {str(e)}"}
