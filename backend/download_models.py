import easyocr
from sentence_transformers import SentenceTransformer
import torch

def download_models():
    print("--- Pre-downloading AI Models ---")
    
    # 1. EasyOCR
    print("Downloading EasyOCR models (detection & recognition)...")
    easyocr.Reader(['en'], gpu=torch.cuda.is_available())
    
    # 2. Sentence Transformers
    print("Downloading Sentence-Transformer model (all-MiniLM-L6-v2)...")
    SentenceTransformer('all-MiniLM-L6-v2')
    
    print("--- All models downloaded successfully ---")

if __name__ == "__main__":
    download_models()
