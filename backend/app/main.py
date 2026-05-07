from fastapi import FastAPI

from app.routes.upload import router as upload_router
from app.routes.ocr import router as ocr_router
from app.routes.parse import router as parse_router

app = FastAPI(
    title="AI Verification System",
    version="1.0.0"
)

app.include_router(upload_router)
app.include_router(ocr_router)
app.include_router(parse_router)

@app.get("/")
def root():
    return {"message": "AI Verification Backend Running"}