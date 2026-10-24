
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

app = FastAPI(
    title="PromiseTrace AI",
    description="Track public promises and their supporting evidence",
    version="1.0.0"
)


class ScanRequest(BaseModel):
    url: HttpUrl


@app.get("/")
def home():
    return {
        "message": "PromiseTrace AI backend is running!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.post("/scan")
def scan_website(request: ScanRequest):
    return {
        "institution_url": str(request.url),
        "status": "pending",
        "claims": [],
        "message": "Scan endpoint ready for TinyFish integration"
    }
