import os
import time
import base64
import requests
import fitz  # PyMuPDF
from PIL import Image
import io
import easyocr
from app.config import settings

# Initialize EasyOCR reader lazily
_easyocr_reader = None

def get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        # English is default
        _easyocr_reader = easyocr.Reader(['en'])
    return _easyocr_reader

def extract_text_with_nvidia(image_bytes):
    """Primary OCR using NVIDIA NIM API"""
    if not settings.NVIDIA_API_KEY:
        return None, "NVIDIA API Key not configured"
    
    image_b64 = base64.b64encode(image_bytes).decode()
    
    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
        "Accept": "application/json"
    }
    
    payload = {
        "input": [{"type": "image_url", "url": f"data:image/png;base64,{image_b64}"}]
    }
    
    try:
        response = requests.post(settings.NVIDIA_OCR_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        extracted_text = ""
        
        # Parse NVIDIA response format
        for item in data.get("data", []):
            for detection in item.get("text_detections", []):
                text = detection.get("text_prediction", {}).get("text", "")
                extracted_text += text + " "
                
        return extracted_text.strip(), None
    except Exception as e:
        return None, str(e)

def extract_text_with_easyocr(image_bytes):
    """Fallback OCR using EasyOCR"""
    try:
        reader = get_easyocr_reader()
        # EasyOCR can take bytes directly
        results = reader.readtext(image_bytes)
        text = " ".join([res[1] for res in results])
        return text, None
    except Exception as e:
        return None, str(e)

def process_file(file_path):
    """Main orchestrator for OCR extraction"""
    ext = os.path.splitext(file_path)[1].lower()
    full_text = ""
    metadata = {
        "provider": "nvidia",
        "fallback_used": False,
        "pages": 0
    }

    # Convert PDF or Image to list of image bytes
    image_pages = []
    if ext == ".pdf":
        doc = fitz.open(file_path)
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Higher resolution
            image_pages.append(pix.tobytes("png"))
        doc.close()
    else:
        with open(file_path, "rb") as f:
            image_pages.append(f.read())

    # Process each page
    for i, img_bytes in enumerate(image_pages):
        # Try NVIDIA first
        text, error = extract_text_with_nvidia(img_bytes)
        
        # If NVIDIA fails or is empty, try EasyOCR fallback
        if (not text or error) and settings.FALLBACK_OCR_ENABLED:
            text, fallback_error = extract_text_with_easyocr(img_bytes)
            metadata["fallback_used"] = True
            metadata["provider"] = "easyocr"
            if not text:
                text = f"[Error on page {i+1}: {error or fallback_error}]"
        
        full_text += f"\n--- Page {i+1} ---\n{text}\n"
        metadata["pages"] += 1

    return full_text.strip(), metadata
