from fastapi import FastAPI

try:
    # When running from backend directory
    from app.routes.upload import router as upload_router
    from app.routes.ocr import router as ocr_router
    from app.routes.parse import router as parse_router
except ModuleNotFoundError:
    # When running from workspace root
    from backend.app.routes.upload import router as upload_router
    from backend.app.routes.ocr import router as ocr_router
    from backend.app.routes.parse import router as parse_router

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