
from backend.evidence_matcher import match_evidence


def test_no_evidence():
    claim = match_evidence(
        claim_text="95% students were placed",
        claim_type="Placement",
        source_url="https://example.com/placements",
        evidence=[]
    )

    assert claim.status == "no_public_evidence_found"
    assert claim.evidence == []
