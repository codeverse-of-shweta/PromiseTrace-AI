
from backend.schemas import Claim, Evidence


def match_evidence(
    claim_text: str,
    claim_type: str,
    source_url: str,
    evidence: list[Evidence]
) -> Claim:
    """
    Creates a claim record with its collected evidence.

    This first version does not automatically decide
    whether the claim is true or false.
    """

    if not evidence:
        status = "no_public_evidence_found"
    elif all(item.source_url == source_url for item in evidence):
        status = "self_reported_only"
    else:
        # External sources exist, but support has not
        # yet been evaluated.
        status = "partially_supported"

    return Claim(
        claim_text=claim_text,
        claim_type=claim_type,
        source_url=source_url,
        status=status,
        evidence=evidence
    )
