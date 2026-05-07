from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "AI Verification System"
    VERSION: str = "1.0.0"
    
    # API Keys
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    
    # OCR Settings
    NVIDIA_OCR_URL: str = "https://ai.api.nvidia.com/v1/cv/nvidia/nemoretriever-ocr-v1"
    FALLBACK_OCR_ENABLED: bool = True
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Paths
    UPLOAD_DIR: str = "app/uploads"

    class Config:
        case_sensitive = True

settings = Settings()

# Ensure upload directory exists
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)
