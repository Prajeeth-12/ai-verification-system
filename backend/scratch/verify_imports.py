import sys
import os

# Add the backend directory to path
sys.path.append(os.getcwd())

try:
    from app.services.ocr_service import process_document
    print("OCR Service import successful")
    from app.routes.ocr import router
    print("OCR Route import successful")
    from app.routes.workflow import router
    print("Workflow Route import successful")
    from app.services.agent_service import run_verification_workflow
    print("Agent Service import successful")
except Exception as e:
    print(f"Import failed: {str(e)}")
    import traceback
    traceback.print_exc()
