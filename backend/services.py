
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
