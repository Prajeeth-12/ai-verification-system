"""
Enterprise-grade hybrid OCR service using NVIDIA NIM as primary engine.

Architecture:
    NVIDIA NIM OCR (Primary) → EasyOCR (Fallback) → Structured Text Output

Why NVIDIA NIM is primary:
    - Production-grade API with SLA guarantees
    - Specialized for document OCR (nemotron-ocr-v1)
    - Better accuracy on complex documents (PDFs, scanned docs)
    - Enterprise security and compliance
    
Why EasyOCR fallback:
    - Ensures local processing if API unavailable
    - No dependency on external services
    - Cost-effective for non-critical documents
    
Future extensibility:
    - Table extraction via NVIDIA Table Understanding API
    - Layout parsing for complex documents
    - Multilingual support expansion
"""

import easyocr
import fitz
import requests
import base64
import io
import os
import time
from PIL import Image
from typing import Dict, Tuple, Optional
from datetime import datetime

from app.config import (
    NVIDIA_API_KEY,
    NVIDIA_OCR_API_URL,
    NVIDIA_OCR_TIMEOUT,
    OCR_FALLBACK_ENABLED,
    MAX_IMAGE_SIZE
)

# Initialize EasyOCR reader (lazy loaded)
_ocr_reader = None

def get_easyocr_reader():
    """Lazy load EasyOCR reader to avoid startup overhead"""
    global _ocr_reader
    if _ocr_reader is None:
        _ocr_reader = easyocr.Reader(['en'])
    return _ocr_reader

# ============================================================================
# NVIDIA NIM OCR Functions
# ============================================================================

def extract_text_with_nvidia(image_path: str) -> Tuple[str, Dict]:
    """
    Extract text from image using NVIDIA NIM OCR API.
    
    Args:
        image_path: Path to image file (PNG, JPG, JPEG)
    
    Returns:
        Tuple of (extracted_text, metadata)
        
    Metadata includes:
        - provider: 'nvidia'
        - timestamp: extraction timestamp
        - success: whether extraction succeeded
        - error: error message if failed
    """
    metadata = {
        "provider": "nvidia",
        "timestamp": datetime.now().isoformat(),
        "model": "nemotron-ocr-v1",
        "success": False
    }
    
    try:
        # Validate file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Read and encode image as base64
        with open(image_path, "rb") as f:
            image_data = f.read()
            image_b64 = base64.b64encode(image_data).decode()
        
        # Check size constraint
        if len(image_b64) > MAX_IMAGE_SIZE:
            raise ValueError(
                f"Image size exceeds limit ({len(image_b64)} > {MAX_IMAGE_SIZE}). "
                "Use NVIDIA Assets API for larger images."
            )
        
        # Prepare API request
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Accept": "application/json"
        }
        
        payload = {
            "input": [
                {
                    "type": "image_url",
                    "url": f"data:image/png;base64,{image_b64}"
                }
            ]
        }
        
        # Call NVIDIA OCR API
        print("[DEBUG] CALLING NVIDIA OCR for:", image_path)
        start_time = time.time()
        response = requests.post(
            NVIDIA_OCR_API_URL,
            headers=headers,
            json=payload,
            timeout=NVIDIA_OCR_TIMEOUT
        )
        extraction_time = time.time() - start_time
        
        response.raise_for_status()
        
        # Parse response - NVIDIA returns data.text_detections format
        result = response.json()
        
        # Extract text from API response
        # NVIDIA format: {"data": [{"text_detections": [{"text_prediction": {"text": "..."}}]}]}
        extracted_text = ""
        if "data" in result and isinstance(result["data"], list):
            for item in result["data"]:
                if "text_detections" in item and isinstance(item["text_detections"], list):
                    for detection in item["text_detections"]:
                        if "text_prediction" in detection:
                            text_obj = detection["text_prediction"]
                            if "text" in text_obj:
                                extracted_text += text_obj["text"] + " "
        
        extracted_text = extracted_text.strip()
        
        print("[DEBUG] NVIDIA OCR succeeded! Text length:", len(extracted_text))
        metadata["success"] = True
        metadata["extraction_time_ms"] = round(extraction_time * 1000, 2)
        
        return extracted_text, metadata
    
    except requests.Timeout:
        metadata["error"] = "NVIDIA API timeout"
        metadata["error_type"] = "timeout"
        return "", metadata
    
    except requests.ConnectionError:
        metadata["error"] = "NVIDIA API connection failed"
        metadata["error_type"] = "connection"
        return "", metadata
    
    except requests.HTTPError as e:
        metadata["error"] = f"NVIDIA API error: {str(e)}"
        metadata["error_type"] = "http_error"
        metadata["status_code"] = response.status_code if 'response' in locals() else None
        return "", metadata
    
    except Exception as e:
        metadata["error"] = f"NVIDIA OCR failed: {str(e)}"
        metadata["error_type"] = "unknown"
        return "", metadata

# ============================================================================
# EasyOCR Fallback Functions
# ============================================================================

def extract_text_with_easyocr(image_path: str) -> Tuple[str, Dict]:
    """
    Extract text from image using EasyOCR (fallback engine).
    
    Args:
        image_path: Path to image file
    
    Returns:
        Tuple of (extracted_text, metadata)
    """
    metadata = {
        "provider": "easyocr",
        "timestamp": datetime.now().isoformat(),
        "success": False
    }
    
    try:
        print("[DEBUG] CALLING EASYOCR for:", image_path)
        reader = get_easyocr_reader()
        
        start_time = time.time()
        results = reader.readtext(image_path)
        extraction_time = time.time() - start_time
        
        # Combine all detected text
        extracted_text = " ".join([text[1] for text in results])
        
        print("[DEBUG] EASYOCR succeeded! Text length:", len(extracted_text))
        metadata["success"] = True
        metadata["extraction_time_ms"] = round(extraction_time * 1000, 2)
        metadata["text_blocks_detected"] = len(results)
        
        return extracted_text, metadata
    
    except Exception as e:
        metadata["error"] = f"EasyOCR failed: {str(e)}"
        metadata["error_type"] = "easyocr_error"
        return "", metadata

# ============================================================================
# PDF Processing
# ============================================================================

def extract_text_from_pdf(pdf_path: str) -> Tuple[str, Dict]:
    """
    Extract text from PDF by converting pages to images and processing with OCR.
    
    Uses hybrid approach: tries NVIDIA first, falls back to EasyOCR if needed.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Tuple of (extracted_text, metadata)
    """
    metadata = {
        "document_type": "pdf",
        "timestamp": datetime.now().isoformat(),
        "pages_processed": 0,
        "providers_used": [],
        "provider": None,
        "success": False
    }
    
    try:
        # Open PDF
        doc = fitz.open(pdf_path)
        full_text = ""
        temp_image_path = "temp_page.png"
        
        # Process each page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))
            image.save(temp_image_path)
            
            # Try NVIDIA first
            text, page_metadata = extract_text_with_nvidia(temp_image_path)
            
            # Fallback to EasyOCR if NVIDIA fails
            if not page_metadata["success"] and OCR_FALLBACK_ENABLED:
                text, fallback_metadata = extract_text_with_easyocr(temp_image_path)
                page_metadata = fallback_metadata
            
            # Track which providers were used
            if page_metadata["provider"] not in metadata["providers_used"]:
                metadata["providers_used"].append(page_metadata["provider"])
            
            # Set top-level provider to first successful extraction method
            if metadata["provider"] is None and page_metadata["success"]:
                metadata["provider"] = page_metadata["provider"]
                metadata["success"] = True
            
            full_text += f"[Page {page_num + 1}]\n{text}\n\n"
            metadata["pages_processed"] += 1
        
        # Cleanup
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        
        return full_text, metadata
    
    except Exception as e:
        metadata["error"] = f"PDF processing failed: {str(e)}"
        metadata["success"] = False
        return "", metadata

# ============================================================================
# Image Processing
# ============================================================================

def extract_text_from_image(image_path: str) -> Tuple[str, Dict]:
    """
    Extract text from image using hybrid NVIDIA + EasyOCR approach.
    
    Flow:
        1. Try NVIDIA NIM OCR API (primary)
        2. If fails, use EasyOCR (fallback) if enabled
        3. Return text + metadata about which provider succeeded
    
    Args:
        image_path: Path to image file (PNG, JPG, JPEG)
    
    Returns:
        Tuple of (extracted_text, metadata)
    """
    metadata = {
        "document_type": "image",
        "timestamp": datetime.now().isoformat(),
        "success": False
    }
    
    try:
        # PRIMARY: Try NVIDIA NIM OCR
        print(f"[DEBUG] extract_text_from_image() called with: {image_path}")
        text, nvidia_metadata = extract_text_with_nvidia(image_path)
        
        if nvidia_metadata["success"]:
            print("[DEBUG] Image extraction: NVIDIA succeeded")
            metadata.update(nvidia_metadata)
            metadata["success"] = True
            return text, metadata
        
        # FALLBACK: Use EasyOCR if NVIDIA failed and fallback enabled
        print(f"[DEBUG] Image extraction: NVIDIA failed, error = {nvidia_metadata.get('error')}")
        if OCR_FALLBACK_ENABLED:
            print("[DEBUG] Image extraction: Trying EasyOCR fallback...")
            text, easyocr_metadata = extract_text_with_easyocr(image_path)
            
            if easyocr_metadata["success"]:
                print("[DEBUG] Image extraction: EasyOCR fallback succeeded")
                metadata.update(easyocr_metadata)
                metadata["fallback_reason"] = nvidia_metadata.get("error")
                metadata["success"] = True
                return text, metadata
        
        # Both methods failed
        metadata["error"] = "All OCR providers failed"
        metadata["nvidia_error"] = nvidia_metadata.get("error")
        metadata["easyocr_error"] = metadata.get("error") if not OCR_FALLBACK_ENABLED else None
        metadata["success"] = False
        
        return "", metadata
    
    except Exception as e:
        metadata["error"] = f"Image OCR orchestration failed: {str(e)}"
        metadata["success"] = False
        return "", metadata

# ============================================================================
# Main Orchestrator
# ============================================================================

def extract_text(file_path: str) -> Tuple[str, Dict]:
    """
    Smart orchestrator function - routes to appropriate extraction method.
    
    Args:
        file_path: Path to document (PDF, PNG, JPG, JPEG)
    
    Returns:
        Tuple of (extracted_text, metadata)
    """
    if not os.path.exists(file_path):
        return "", {
            "error": f"File not found: {file_path}",
            "success": False
        }
    
    extension = os.path.splitext(file_path)[1].lower()
    
    if extension == ".pdf":
        return extract_text_from_pdf(file_path)
    elif extension in [".png", ".jpg", ".jpeg"]:
        return extract_text_from_image(file_path)
    else:
        return "", {
            "error": f"Unsupported file type: {extension}",
            "success": False
        }
