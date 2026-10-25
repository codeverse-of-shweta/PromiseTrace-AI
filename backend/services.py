
from tinyfish.main import collect_claims
def get_institution_claims(institution_url: str) -> dict:
    return collect_claims(institution_url)
