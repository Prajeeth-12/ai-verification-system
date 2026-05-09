import requests
import json
from app.config import settings
from app.utils.prompts import get_parsing_prompt

def parse_with_ai(doc_type, ocr_text):
    """
    Parses OCR text into structured JSON using NVIDIA NIM LLM.
    """
    if not settings.NVIDIA_API_KEY:
        return {"error": "NVIDIA API Key not configured"}
    
    prompt = get_parsing_prompt(doc_type, ocr_text)
    
    # NVIDIA NIM LLM Endpoint (Generic chat completion)
    # Note: Model name from roadmap
    url = "https://ai.api.nvidia.com/v1/genai/nvidia/nemotron-3-super-120b-a12b"
    
    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
        "Accept": "application/json"
    }
    
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "top_p": 0.7,
        "max_tokens": 1024
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Clean JSON response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        return json.loads(content)
    except Exception as e:
        return {"error": f"AI Parsing failed: {str(e)}", "raw_content": content if 'content' in locals() else None}
