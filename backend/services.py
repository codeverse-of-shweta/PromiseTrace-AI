
from tinyfish.main import collect_claims
def get_institution_claims(institution_url: str) -> dict:
    return collect_claims(institution_url)
from backend.schemas import ScanResponse


def scan_institution(url: str) -> ScanResponse:
    """
    Coordinates the institution scan workflow.

    TinyFish collection and evidence matching
    will be connected when those modules are ready.
    """
    return ScanResponse(
        institution_url=url,
        status="pending",
        claims=[],
        message="Waiting for claim collector and evidence matcher integration"
    )
