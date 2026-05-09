from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from pathlib import Path

# Calculate the base directory of the backend
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = os.path.join(BASE_DIR, ".env")

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: Optional[str] = None
    NVIDIA_API_KEY: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    
    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    # NVIDIA NIM OCR Configuration
    NVIDIA_OCR_API_URL: str = "https://ai.api.nvidia.com/v1/cv/nvidia/nemoretriever-ocr-v1"
    NVIDIA_OCR_MODEL: str = "nemoretriever-ocr-v1"
    NVIDIA_OCR_TIMEOUT: int = 30
    
    # OCR Configuration
    OCR_FALLBACK_ENABLED: bool = True
    OCR_MAX_RETRIES: int = 2
    OCR_TIMEOUT: int = 30
    MAX_IMAGE_SIZE: int = 180_000
    
    # Use absolute path for env_file to ensure it's found regardless of CWD
    model_config = SettingsConfigDict(
        env_file=ENV_PATH, 
        extra="ignore",
        case_sensitive=True
    )

settings = Settings()

# Global exports for backward compatibility
GEMINI_API_KEY = settings.GEMINI_API_KEY
NVIDIA_API_KEY = settings.NVIDIA_API_KEY
DATABASE_URL = settings.DATABASE_URL
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY
SUPABASE_SERVICE_ROLE_KEY = settings.SUPABASE_SERVICE_ROLE_KEY

NVIDIA_OCR_API_URL = settings.NVIDIA_OCR_API_URL
NVIDIA_OCR_MODEL = settings.NVIDIA_OCR_MODEL
NVIDIA_OCR_TIMEOUT = settings.NVIDIA_OCR_TIMEOUT

OCR_FALLBACK_ENABLED = settings.OCR_FALLBACK_ENABLED
OCR_MAX_RETRIES = settings.OCR_MAX_RETRIES
OCR_TIMEOUT = settings.OCR_TIMEOUT
MAX_IMAGE_SIZE = settings.MAX_IMAGE_SIZE
