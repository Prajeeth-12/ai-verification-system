from dotenv import load_dotenv
import os

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

# NVIDIA NIM OCR Configuration
NVIDIA_OCR_API_URL = "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v1"
NVIDIA_OCR_MODEL = "nemotron-ocr-v1"
NVIDIA_OCR_TIMEOUT = 30  # seconds

# OCR Configuration
OCR_FALLBACK_ENABLED = True  # Use EasyOCR as fallback if NVIDIA fails
OCR_MAX_RETRIES = 2
OCR_TIMEOUT = 30
MAX_IMAGE_SIZE = 180_000  # Base64 character limit for NVIDIA API
