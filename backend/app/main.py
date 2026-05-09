from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.routes.upload import router as upload_router
from app.routes.ocr import router as ocr_router
from app.routes.parse import router as parse_router
from app.routes.workflow import router as workflow_router
from app.routes.semantic_verify import router as semantic_router
from app.routes.report import router as report_router

app = FastAPI(
    title="AI Verification System",
    version="1.0.0"
)

# Add CORS middleware to allow requests from browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(upload_router)
app.include_router(ocr_router)
app.include_router(parse_router)
app.include_router(workflow_router)
app.include_router(semantic_router)
app.include_router(report_router)

@app.get("/")
def root():
    return {"message": "AI Verification Backend Running"}