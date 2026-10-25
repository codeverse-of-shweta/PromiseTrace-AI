import json
import os
from typing import Any
from urllib.parse import urlparse

import requests


TINYFISH_ENDPOINT = "https://agent.tinyfish.ai/v1/automation/run-sse"
DEFAULT_TIMEOUT = (10, 600)


class TinyFishError(RuntimeError):
    """Raised when TinyFish returns an invalid or unsuccessful response."""


def _validate_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        raise ValueError("institution_url must be a non-empty URL.")

    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("institution_url must be a valid HTTP(S) URL.")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing embedded credentials are not allowed.")

    return url


def _parse_sse_line(line: str) -> dict[str, Any] | None:
    """Parse one SSE data line; ignore comments and unrelated lines."""
    if not line.startswith("data:"):
        return None

    payload = line[len("data:"):].strip()

    if not payload or payload == "[DONE]":
        return None

    try:
        event = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise TinyFishError("TinyFish returned malformed SSE JSON.") from exc

    if not isinstance(event, dict):
        raise TinyFishError("TinyFish SSE event must be a JSON object.")

    return event


def _extract_result(event: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a successful COMPLETE event."""
    result = event.get("result")

    if not isinstance(result, dict):
        raise TinyFishError("COMPLETE event is missing a valid result object.")

    findings = result.get("findings")
    if not isinstance(findings, list):
        raise TinyFishError("TinyFish result is missing the findings list.")

    claims = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue

        claim_text = finding.get("claim_text")
        if not isinstance(claim_text, str) or not claim_text.strip():
            continue

        claims.append({
            "type": finding.get("type"),
            "claim_text": claim_text.strip(),
            "source_url": finding.get("page_url"),
            "year_mentioned": finding.get("year_mentioned"),
            "category": finding.get("category"),
        })

    summary = result.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}

    return {
        "status": "completed",
        "run_id": event.get("run_id"),
        "claims": claims,
        "summary": summary,
        "note": result.get("note"),
    }


def collect_claims(institution_url: str) -> dict[str, Any]:
    """
    Run TinyFish against an institution URL and return structured claims.

    Raises:
        ValueError: Invalid institution URL.
        TinyFishError: Missing API key, HTTP/SSE failure, malformed
            response, or missing results.
    """
    institution_url = _validate_url(institution_url)

    api_key = os.environ.get("TINYFISH_API_KEY", "").strip()
    if not api_key:
        raise TinyFishError(
            "TINYFISH_API_KEY is not set in the environment."
        )

    payload = {
        "url": institution_url,
        "goal": (
            "Visit the institution's official website. Find publicly stated "
            "placement statistics, industry partnerships, internship and "
            "career claims. Return a JSON result with a findings list. Each "
            "finding should include type, claim_text, page_url, "
            "year_mentioned, and category. Include a summary and note. "
            "Do not invent missing statistics; state when data is unavailable."
        ),
    }

    try:
        with requests.post(
            TINYFISH_ENDPOINT,
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            },
            json=payload,
            stream=True,
            timeout=DEFAULT_TIMEOUT,
        ) as response:
            if not response.ok:
                # Do not include request headers or API keys in exceptions.
                detail = response.text[:500]
                raise TinyFishError(
                    f"TinyFish HTTP error {response.status_code}: {detail}"
                )

            complete_event = None
            error_event = None

            for raw_line in response.iter_lines(decode_unicode=True):
                if raw_line is None:
                    continue
                if isinstance(raw_line, bytes):
                    raw_line = raw_line.decode("utf-8", errors="replace")

                line = raw_line.strip()
                if not line:
                    continue

                event = _parse_sse_line(line)
                if event is None:
                    continue

                event_type = str(event.get("type", "")).upper()

                if event_type in {"ERROR", "FAILED"}:
                    error_event = event
                    break

                if event_type == "COMPLETE":
                    complete_event = event
                    break

            if error_event is not None:
                message = error_event.get("message") or error_event.get("error")
                raise TinyFishError(
                    f"TinyFish run failed: {message or 'unspecified error'}"
                )

            if complete_event is None:
                raise TinyFishError(
                    "TinyFish stream ended without a COMPLETE event."
                )

            if str(complete_event.get("status", "")).upper() not in {
                "COMPLETED", "SUCCESS", "SUCCEEDED"
            }:
                raise TinyFishError(
                    "TinyFish COMPLETE event did not report success."
                )

            result = _extract_result(complete_event)
            result["institution_url"] = institution_url
            return result

    except requests.Timeout as exc:
        raise TinyFishError("TinyFish request timed out.") from exc
    except requests.RequestException as exc:
        raise TinyFishError(f"TinyFish request failed: {exc}") from exc


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Collect institution claims.")
    parser.add_argument("institution_url", help="Official institution URL")
    args = parser.parse_args()

    try:
        print(json.dumps(collect_claims(args.institution_url), indent=2))
    except (ValueError, TinyFishError) as exc:
        raise SystemExit(str(exc)) from exc
