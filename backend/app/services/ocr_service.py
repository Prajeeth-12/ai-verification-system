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
import tempfile
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

def get_temp_image_path():
    """Get a safe temporary path for image files"""
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, f"ocr_page_{int(time.time()*1000)}.png")

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
        print(f"[DEBUG] NVIDIA_API_KEY present: {bool(NVIDIA_API_KEY)}")
        print(f"[DEBUG] NVIDIA_OCR_API_URL: {NVIDIA_OCR_API_URL}")
        start_time = time.time()
        response = requests.post(
            NVIDIA_OCR_API_URL,
            headers=headers,
            json=payload,
            timeout=NVIDIA_OCR_TIMEOUT
        )
        extraction_time = time.time() - start_time
        print(f"[DEBUG] NVIDIA API response status: {response.status_code}")
        
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
        "success": False,
        "fallback_used": False,
        "fallback_reason": None,
        "nvidia_attempted": False
    }
    
    try:
        # Open PDF
        print(f"[DEBUG] Opening PDF: {pdf_path}")
        doc = fitz.open(pdf_path)
        full_text = ""
        
        # Process each page
        for page_num in range(len(doc)):
            # Get temp path with proper directory
            temp_image_path = get_temp_image_path()
            print(f"[DEBUG] Processing PDF page {page_num + 1}, temp path: {temp_image_path}")
            
            try:
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                img_bytes = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_bytes))
                image.save(temp_image_path)
                print(f"[DEBUG] Saved page image: {temp_image_path}, size: {os.path.getsize(temp_image_path)} bytes")
                
                # Use unified image handler - ensures consistency with image OCR path
                text, page_metadata = extract_text_from_image(temp_image_path)
                print(f"[DEBUG] Page {page_num + 1} extraction result: provider={page_metadata.get('provider')}, success={page_metadata.get('success')}")
                
                # Track whether NVIDIA was attempted
                if page_metadata.get("nvidia_attempted"):
                    metadata["nvidia_attempted"] = True

                # Track which providers were used
                if page_metadata.get("provider") and page_metadata["provider"] not in metadata["providers_used"]:
                    metadata["providers_used"].append(page_metadata["provider"])
                
                # Set top-level provider to first successful extraction method
                if metadata["provider"] is None and page_metadata.get("success"):
                    metadata["provider"] = page_metadata.get("provider")
                    metadata["success"] = True

                # Track fallback usage
                if page_metadata.get("fallback_used"):
                    metadata["fallback_used"] = True
                    if not metadata["fallback_reason"]:
                        metadata["fallback_reason"] = page_metadata.get("fallback_reason")
                
                full_text += f"[Page {page_num + 1}]\n{text}\n\n"
                metadata["pages_processed"] += 1
            
            finally:
                # Always cleanup temp file
                if os.path.exists(temp_image_path):
                    try:
                        os.remove(temp_image_path)
                        print(f"[DEBUG] Cleaned up temp file: {temp_image_path}")
                    except Exception as e:
                        print(f"[DEBUG] Failed to cleanup temp file: {e}")
        
        # If no successful provider was set but providers were used, set provider for visibility
        if metadata["provider"] is None and metadata["providers_used"]:
            metadata["provider"] = metadata["providers_used"][0]

        print(f"[DEBUG] PDF processing complete. Provider: {metadata['provider']}, Pages: {metadata['pages_processed']}")
        return full_text, metadata
    
    except Exception as e:
        print(f"[DEBUG] PDF processing failed: {e}")
        import traceback
        traceback.print_exc()
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
        "success": False,
        "fallback_used": False,
        "fallback_reason": None,
        "nvidia_attempted": True
    }
    
    try:
        # PRIMARY: Try NVIDIA NIM OCR
        print(f"[DEBUG] extract_text_from_image() called with: {image_path}")
        text, nvidia_metadata = extract_text_with_nvidia(image_path)
        
        # Check if NVIDIA succeeded AND extracted meaningful text
        if nvidia_metadata["success"] and text.strip():
            print("[DEBUG] Image extraction: NVIDIA succeeded with text")
            metadata.update(nvidia_metadata)
            metadata["success"] = True
            return text, metadata
        
        # FALLBACK: Use EasyOCR if NVIDIA failed OR got empty text
        if not nvidia_metadata["success"]:
            print(f"[DEBUG] Image extraction: NVIDIA failed, error = {nvidia_metadata.get('error')}")
        else:
            print(f"[DEBUG] Image extraction: NVIDIA returned empty text, trying fallback...")
        
        if OCR_FALLBACK_ENABLED:
            print("[DEBUG] Image extraction: Trying EasyOCR fallback...")
            text, easyocr_metadata = extract_text_with_easyocr(image_path)
            
            if easyocr_metadata["success"]:
                print("[DEBUG] Image extraction: EasyOCR fallback succeeded")
                metadata.update(easyocr_metadata)
                metadata["fallback_used"] = True
                metadata["fallback_reason"] = nvidia_metadata.get("error") or "NVIDIA returned empty text"
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

def process_document(url_or_path: str) -> Tuple[str, Dict]:
    """
    Higher-level orchestrator that handles both local paths and remote URLs.
    Downloads remote files to a temporary location before processing.
    """
    is_url = url_or_path.startswith("http://") or url_or_path.startswith("https://")
    
    if not is_url:
        return extract_text(url_or_path)
        
    # Handle URL
    print(f"[DEBUG] process_document: Downloading from URL: {url_or_path}")
    temp_path = None
    try:
        # Determine extension from URL or use PDF as default
        ext = ".pdf"
        if ".png" in url_or_path.lower(): ext = ".png"
        elif ".jpg" in url_or_path.lower(): ext = ".jpg"
        elif ".jpeg" in url_or_path.lower(): ext = ".jpeg"
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            temp_path = tmp.name
            
        # Download
        response = requests.get(url_or_path, timeout=30)
        response.raise_for_status()
        
        with open(temp_path, "wb") as f:
            f.write(response.content)
            
        print(f"[DEBUG] Downloaded to: {temp_path}, size: {os.path.getsize(temp_path)}")
        
        # Process
        text, metadata = extract_text(temp_path)
        return text, metadata
        
    except Exception as e:
        print(f"[ERROR] process_document (URL) failed: {e}")
        return "", {"success": False, "error": str(e), "provider": "orchestrator"}
        
    finally:
        # Cleanup
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
