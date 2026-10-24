
from pydantic import BaseModel, HttpUrl, Field
from typing import Literal


class ScanRequest(BaseModel):
    url: HttpUrl


class Evidence(BaseModel):
    source_url: str
    snippet: str
    source_type: str = "unknown"


class Claim(BaseModel):
    claim_text: str
    claim_type: str
    source_url: str
    status: Literal[
        "corroborated",
        "partially_supported",
        "self_reported_only",
        "no_public_evidence_found",
        "contradicted"
    ] = "no_public_evidence_found"
    evidence: list[Evidence] = Field(default_factory=list)


class ScanResponse(BaseModel):
    institution_url: str
    status: Literal["pending", "completed", "failed"]
    claims: list[Claim] = Field(default_factory=list)
    message: str = ""
