import requests
import json
import re
import logging
from typing import Dict, Any, Optional
from app.config import settings

# Configure structured logging
logger = logging.getLogger(__name__)

def parse_document_text(ocr_text: str, document_type: str) -> Dict[str, Any]:
    """
    Parses OCR text into structured JSON using NVIDIA Nemotron LLM.
    Includes regex fallbacks for critical ID extraction.
    """
    logger.info(f"Starting structured parsing for document type: {document_type}")
    
    if not settings.NVIDIA_API_KEY:
        logger.error("NVIDIA API Key is missing from configuration")
        return {"success": False, "error": "NVIDIA API Key not configured"}

    # 1. Prepare Prompt
    prompt = _get_specialized_prompt(document_type, ocr_text)
    
    # 2. Call NVIDIA Nemotron LLM
    # Using Llama-3.1-Nemotron-70B-Instruct as the modern standard
    url = "https://ai.api.nvidia.com/v1/genai/nvidia/llama-3.1-nemotron-70b-instruct"
    
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
    
    parsing_result = {
        "success": False,
        "data": {},
        "metadata": {
            "provider": "nvidia-nemotron",
            "document_type": document_type,
            "fallback_used": False
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        # Fallback to the older endpoint if the new one fails (for compatibility)
        if response.status_code == 404:
            logger.warning("Modern Nemotron endpoint not found, falling back to legacy")
            url = "https://ai.api.nvidia.com/v1/genai/nvidia/nemotron-3-super-120b-a12b"
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
        response.raise_for_status()
        
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # 3. Parse and Clean JSON
        parsed_data = _clean_and_parse_json(content)
        if parsed_data:
            parsing_result["success"] = True
            parsing_result["data"] = parsed_data
            logger.info(f"Successfully parsed {document_type} with LLM")
        else:
            logger.warning(f"LLM returned invalid JSON for {document_type}: {content[:100]}...")
            
    except Exception as e:
        logger.error(f"NVIDIA LLM call failed: {str(e)}")
        parsing_result["error"] = f"LLM call failed: {str(e)}"

    # 4. Fallback Regex Extraction for Critical IDs
    fallback_data = _apply_regex_fallback(ocr_text, document_type)
    if fallback_data:
        # Merge fallback data if LLM failed or missed critical fields
        for key, value in fallback_data.items():
            if not parsing_result["data"].get(key):
                parsing_result["data"][key] = value
                parsing_result["metadata"]["fallback_used"] = True
                logger.info(f"Regex fallback applied for field: {key}")

    # 5. Validation and Missing Fields Logging
    _log_parsing_status(parsing_result, document_type)
    
    return parsing_result

def _get_specialized_prompt(doc_type: str, text: str) -> str:
    """
    Generates specialized extraction instructions for different document types.
    """
    field_specs = {
        "aadhaar": {
            "fields": "name, dob (DD-MM-YYYY), gender, aadhaar_number (12 digits)",
            "example": '{"name": "John Doe", "dob": "01-01-1990", "gender": "Male", "aadhaar_number": "123456789012"}'
        },
        "pan": {
            "fields": "name, father_name, dob (DD-MM-YYYY), pan_number (10 alphanumeric characters)",
            "example": '{"name": "John Doe", "father_name": "Jane Doe", "dob": "01-01-1990", "pan_number": "ABCDE1234F"}'
        },
        "certificate": {
            "fields": "name, certificate_type, issuing_authority, issue_date",
            "example": '{"name": "John Doe", "certificate_type": "Degree", "issuing_authority": "University", "issue_date": "2023"}'
        },
        "resume": {
            "fields": "name, email, phone, skills (array of strings), education (array of strings or objects)",
            "example": '{"name": "John Doe", "email": "john@example.com", "phone": "1234567890", "skills": ["Python", "AI"], "education": ["B.Tech"]}'
        }
    }
    
    spec = field_specs.get(doc_type.lower(), {"fields": "all names, dates, and identifiers", "example": "{}"})
    
    return f"""
    You are an expert document parser. Your task is to extract information from the following OCR text and return it in a structured JSON format.
    
    DOCUMENT TYPE: {doc_type.upper()}
    
    REQUIRED FIELDS: {spec['fields']}
    
    INSTRUCTIONS:
    - Return ONLY a valid JSON object. No markdown, no conversational text.
    - If a field is not present in the text, use null.
    - Ensure dates are formatted as DD-MM-YYYY if possible.
    - Be precise with ID numbers.
    
    EXAMPLE FORMAT:
    {spec['example']}
    
    OCR TEXT TO PARSE:
    ---
    {text}
    ---
    
    JSON OUTPUT:
    """

def _clean_and_parse_json(content: str) -> Optional[Dict[str, Any]]:
    """
    Cleans LLM response and attempts to parse it as JSON.
    """
    try:
        # Remove markdown code blocks if present
        cleaned = content.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        
        # Try to find the first '{' and last '}'
        start_idx = cleaned.find('{')
        end_idx = cleaned.rfind('}')
        if start_idx != -1 and end_idx != -1:
            cleaned = cleaned[start_idx:end_idx+1]
            
        return json.loads(cleaned)
    except Exception:
        return None

def _apply_regex_fallback(text: str, doc_type: str) -> Dict[str, Any]:
    """
    Regex-based extraction for critical identifiers to ensure high recall.
    """
    extracted = {}
    
    if doc_type.lower() == "aadhaar":
        # Aadhaar: 12 digits, often with spaces
        aadhaar_match = re.search(r'\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b', text)
        if aadhaar_match:
            extracted["aadhaar_number"] = aadhaar_match.group(0).replace(" ", "")
            
    elif doc_type.lower() == "pan":
        # PAN: 5 letters, 4 digits, 1 letter
        pan_match = re.search(r'\b[A-Z]{5}\d{4}[A-Z]\b', text)
        if pan_match:
            extracted["pan_number"] = pan_match.group(0)
            
    # Common fields
    if "email" not in extracted:
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            extracted["email"] = email_match.group(0)

    if "phone" not in extracted:
        phone_match = re.search(r'\b(?:\+91|91)?[6-9]\d{9}\b', text)
        if phone_match:
            extracted["phone"] = phone_match.group(0)
        
    return extracted

def _log_parsing_status(result: Dict[str, Any], doc_type: str):
    """
    Structured logging for parsing outcomes.
    """
    if result["success"]:
        logger.info(f"PARSING_SUCCESS: Document={doc_type}, FieldsExtracted={list(result['data'].keys())}")
    else:
        logger.error(f"PARSING_FAILURE: Document={doc_type}, Error={result.get('error', 'Unknown')}")
        
    # Check for missing required fields
    required = {
        "aadhaar": ["name", "aadhaar_number"],
        "pan": ["name", "pan_number"],
        "certificate": ["name", "issuing_authority"],
        "resume": ["name", "email"]
    }
    
    expected = required.get(doc_type.lower(), [])
    missing = [f for f in expected if not result["data"].get(f)]
    
    if missing:
        logger.warning(f"MISSING_FIELDS: Document={doc_type}, Fields={missing}")
