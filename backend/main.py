
from fastapi import FastAPI, HTTPException
from backend.schemas import ScanRequest, ScanResponse
from backend.services import scan_institution

app = FastAPI(
    title="PromiseTrace AI",
    description="Track public promises and their supporting evidence",
    version="1.0.0"
)


@app.get("/")
def home():
    return {"message": "PromiseTrace AI backend is running!"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/scan", response_model=ScanResponse)
def scan_website(request: ScanRequest):
    return scan_institution(str(request.url))
