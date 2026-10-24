import csv
import json
import re
import sqlite3
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from difflib import SequenceMatcher

INPUT_FILE = Path("claims.json")
DB_FILE = "matched.db"
JSON_REPORT = "report.json"
CSV_REPORT = "report.csv"
REQUEST_TIMEOUT = 12
MAX_BYTES = 2_000_000
MAX_PASSAGES_PER_URL = 120
TOP_EVIDENCE_PER_CLAIM = 3
USER_AGENT = "PromiseTraceAI/0.1 (evidence-retrieval prototype)"

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with",
    "by", "from", "as", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "also", "which", "who",
    "their", "they", "have", "has", "had", "into", "at", "through", "either",
    "both", "such", "can", "may", "will", "designed", "include", "includes",
}


class PageTextParser(HTMLParser):
    BLOCK_TAGS = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "td", "th"}
    SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.current_tag = None
        self.current_parts = []
        self.passages = []
        self.title_parts = []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
        if tag == "title":
            self.in_title = True
        if self.skip_depth == 0 and tag in self.BLOCK_TAGS:
            self._flush()
            self.current_tag = tag

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag in self.SKIP_TAGS and self.skip_depth > 0:
            self.skip_depth -= 1
        if self.skip_depth == 0 and tag in self.BLOCK_TAGS:
            self._flush()

    def handle_data(self, data):
        clean = re.sub(r"\s+", " ", data).strip()
        if not clean:
            return
        if self.in_title:
            self.title_parts.append(clean)
        if self.skip_depth == 0:
            self.current_parts.append(clean)

    def _flush(self):
        text = re.sub(r"\s+", " ", " ".join(self.current_parts)).strip()
        if len(text) >= 25:
            self.passages.append(text)
        self.current_parts = []
        self.current_tag = None

    def finish(self):
        self._flush()
        if not self.passages and self.current_parts:
            text = " ".join(self.current_parts).strip()
            if text:
                self.passages.append(text)
        return " ".join(self.title_parts).strip(), self.passages[:MAX_PASSAGES_PER_URL]


def validate_url(url):
    if not url:
        raise ValueError("No source URL supplied")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Only absolute HTTP/HTTPS source URLs are supported")
    host = (parsed.hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "::1", "0.0.0.0"} or host.endswith(".local"):
        raise ValueError("Local network URLs are not allowed")
    return url


def fetch_page(url):
    try:
        validate_url(url)
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html, text/plain;q=0.9,*/*;q=0.5"})
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "").lower()
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raw = raw[:MAX_BYTES]
            charset_match = re.search(r"charset=([\w.-]+)", content_type)
            charset = charset_match.group(1) if charset_match else "utf-8"
            text = raw.decode(charset, errors="replace")
            if "html" in content_type or "<html" in text[:1000].lower():
                parser = PageTextParser()
                parser.feed(text)
                title, passages = parser.finish()
            else:
                title = ""
                passages = [re.sub(r"\s+", " ", text).strip()] if text.strip() else []
            return {
                "requested_url": url,
                "final_url": final_url,
                "title": title,
                "passages": passages,
                "retrieval_status": "retrieved" if passages else "retrieved_no_text",
                "error": None,
                "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        return {
            "requested_url": url,
            "final_url": None,
            "title": None,
            "passages": [],
            "retrieval_status": "source_unavailable",
            "error": f"{type(exc).__name__}: {exc}",
            "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


def tokens(text):
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {word for word in words if word not in STOPWORDS and len(word) > 1}


def score_passage(claim_text, passage):
    """Combine claim-token coverage and Jaccard overlap; score is not truth probability."""
    claim_tokens = tokens(claim_text)
    passage_tokens = tokens(passage)
    if not claim_tokens or not passage_tokens:
        return 0.0, 0.0, 0.0
    overlap = claim_tokens & passage_tokens
    coverage = len(overlap) / len(claim_tokens)
    jaccard = len(overlap) / len(claim_tokens | passage_tokens)
    sequence = SequenceMatcher(None, (claim_text or "").lower(), (passage or "").lower()).ratio()
    score = min(1.0, 0.65 * coverage + 0.20 * jaccard + 0.15 * sequence)
    return round(score, 3), round(coverage, 3), round(jaccard, 3)


def load_data():
    with INPUT_FILE.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Input JSON must contain a JSON object")
    if not isinstance(data.get("findings"), list):
        raise ValueError("Expected the existing input schema: a top-level 'findings' list")
    for index, finding in enumerate(data["findings"], start=1):
        if not isinstance(finding, dict) or not str(finding.get("claim_text", "")).strip():
            raise ValueError(f"Finding {index} must be an object with a non-empty claim_text")
    return data


def create_database():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("""CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY, claim_text TEXT NOT NULL, claim_type TEXT,
            category TEXT, source_url TEXT, year_mentioned TEXT,
            source_status TEXT NOT NULL, final_status TEXT NOT NULL,
            matching_score REAL, last_checked TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS evidence (
            evidence_id INTEGER PRIMARY KEY AUTOINCREMENT, claim_id TEXT NOT NULL,
            source_title TEXT, source_url TEXT, evidence_text TEXT,
            matching_score REAL, claim_coverage REAL, jaccard_score REAL,
            retrieval_status TEXT, review_status TEXT, retrieval_error TEXT,
            retrieved_at TEXT, FOREIGN KEY (claim_id) REFERENCES claims(claim_id)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS run_summary (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT,
            run_status TEXT, summary_json TEXT, note TEXT, created_at TEXT
        )""")
        claim_columns = {row[1] for row in conn.execute("PRAGMA table_info(claims)")}
        for name, sql_type in [("final_status", "TEXT NOT NULL DEFAULT 'EXTRACTED'"),
                               ("matching_score", "REAL"), ("last_checked", "TEXT")]:
            if name not in claim_columns:
                conn.execute(f"ALTER TABLE claims ADD COLUMN {name} {sql_type}")
        evidence_columns = {row[1] for row in conn.execute("PRAGMA table_info(evidence)")}
        for name, sql_type in [("claim_coverage", "REAL"), ("jaccard_score", "REAL"),
                               ("retrieval_status", "TEXT"), ("retrieval_error", "TEXT"),
                               ("retrieved_at", "TEXT")]:
            if name not in evidence_columns:
                conn.execute(f"ALTER TABLE evidence ADD COLUMN {name} {sql_type}")


def analyze_finding(finding, index, page_cache):
    claim_id = str(finding.get("claim_id") or f"F{index:03d}")
    claim_text = str(finding["claim_text"]).strip()
    urls = finding.get("evidence_urls") or finding.get("source_urls") or [finding.get("page_url")]
    if isinstance(urls, str):
        urls = [urls]
    urls = list(dict.fromkeys(url for url in urls if isinstance(url, str) and url.strip()))

    candidate_evidence = []
    fetch_errors = []
    for url in urls:
        if url not in page_cache:
            page_cache[url] = fetch_page(url)
        page = page_cache[url]
        if page["error"]:
            fetch_errors.append({"url": url, "error": page["error"]})
        for passage in page["passages"]:
            score, coverage, jaccard = score_passage(claim_text, passage)
            candidate_evidence.append({
                "source_title": page["title"],
                "source_url": page["final_url"] or url,
                "evidence_text": passage[:1200],
                "matching_score": score,
                "claim_coverage": coverage,
                "jaccard_score": jaccard,
                "retrieval_status": page["retrieval_status"],
                "retrieval_error": page["error"],
                "retrieved_at": page["retrieved_at"],
            })

    candidate_evidence.sort(key=lambda item: item["matching_score"], reverse=True)
    top = candidate_evidence[:TOP_EVIDENCE_PER_CLAIM]
    best = top[0] if top else None
    if best and best["claim_coverage"] >= 0.75 and best["matching_score"] >= 0.55:
        final_status = "POTENTIALLY_SUPPORTED"
        explanation = "A retrieved passage has substantial wording overlap with the claim; human review is still required."
    elif fetch_errors and not candidate_evidence:
        final_status = "SOURCE_UNAVAILABLE"
        explanation = "The supplied source could not be retrieved; this is not evidence that the claim is false."
    else:
        final_status = "INSUFFICIENT_EVIDENCE"
        explanation = "No retrieved passage met the prototype's similarity threshold; absence of a match does not prove contradiction."

    return {
        "claim_id": claim_id,
        "claim_text": claim_text,
        "type": finding.get("type"),
        "category": finding.get("category"),
        "source_url": finding.get("page_url"),
        "year_mentioned": finding.get("year_mentioned"),
        "source_status": "extracted",
        "final_status": final_status,
        "matching_score": best["matching_score"] if best else None,
        "claim_coverage": best["claim_coverage"] if best else None,
        "best_evidence": best,
        "evidence_passages": top,
        "retrieval_errors": fetch_errors,
        "explanation": explanation,
        "verification_limit": "Similarity is a retrieval aid, not a truth probability. Contradiction is not automatically inferred from missing or low-overlap text.",
    }


def save_to_database(data, results):
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for result in results:
            conn.execute("""INSERT INTO claims (
                claim_id, claim_text, claim_type, category, source_url, year_mentioned,
                source_status, final_status, matching_score, last_checked
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(claim_id) DO UPDATE SET
                claim_text=excluded.claim_text, claim_type=excluded.claim_type,
                category=excluded.category, source_url=excluded.source_url,
                year_mentioned=excluded.year_mentioned, source_status=excluded.source_status,
                final_status=excluded.final_status, matching_score=excluded.matching_score,
                last_checked=excluded.last_checked""", (
                result["claim_id"], result["claim_text"], result["type"], result["category"],
                result["source_url"], str(result["year_mentioned"]) if result["year_mentioned"] is not None else None,
                result["source_status"], result["final_status"], result["matching_score"], now
            ))
            
            conn.execute("DELETE FROM evidence WHERE claim_id = ?", (result["claim_id"],))
            for item in result["evidence_passages"]:
                conn.execute("""INSERT INTO evidence (
                    claim_id, source_title, source_url, evidence_text, matching_score,
                    claim_coverage, jaccard_score, retrieval_status, review_status,
                    retrieval_error, retrieved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    result["claim_id"], item["source_title"], item["source_url"], item["evidence_text"],
                    item["matching_score"], item["claim_coverage"], item["jaccard_score"],
                    item["retrieval_status"], "needs_human_review", item["retrieval_error"], item["retrieved_at"]
                ))
        conn.execute("INSERT INTO run_summary (run_id, run_status, summary_json, note, created_at) VALUES (?, ?, ?, ?, ?)", (
            data.get("run_id"), data.get("status"), json.dumps(data.get("summary", {}), ensure_ascii=False),
            data.get("note"), now
        ))


def export_reports(data, results):
    status_counts = {}
    for result in results:
        status_counts[result["final_status"]] = status_counts.get(result["final_status"], 0) + 1
    output = {
        "run_id": data.get("run_id"),
        "run_status": data.get("status"),
        "findings_processed": len(results),
        "status_counts": status_counts,
        "findings": results,
        "summary": data.get("summary", {}),
        "note": data.get("note"),
        "methodology_note": "Source pages were retrieved and passages ranked by text similarity. Similarity does not establish truth; human review and independent corroboration are required."
    }
    with open(JSON_REPORT, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, ensure_ascii=False)
    fields = ["claim_id", "claim_text", "type", "category", "source_url", "year_mentioned",
              "source_status", "final_status", "matching_score", "claim_coverage", "best_evidence_url",
              "best_evidence_text", "explanation"]
    with open(CSV_REPORT, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            best = result["best_evidence"] or {}
            writer.writerow({
                "claim_id": result["claim_id"], "claim_text": result["claim_text"],
                "type": result["type"], "category": result["category"],
                "source_url": result["source_url"], "year_mentioned": result["year_mentioned"],
                "source_status": result["source_status"], "final_status": result["final_status"],
                "matching_score": result["matching_score"], "claim_coverage": result["claim_coverage"],
                "best_evidence_url": best.get("source_url"), "best_evidence_text": best.get("evidence_text"),
                "explanation": result["explanation"]
            })


def main():
    data = load_data()
    create_database()
    cache = {}
    results = [analyze_finding(finding, index, cache) for index, finding in enumerate(data["findings"], start=1)]
    save_to_database(data, results)
    export_reports(data, results)
    print(f"Findings processed: {len(results)}")
    print("Final statuses:")
    for status in sorted({result['final_status'] for result in results}):
        print(f"  {status}: {sum(result['final_status'] == status for result in results)}")
    print(f"Created: {DB_FILE}, {JSON_REPORT}, {CSV_REPORT}")
    print("Reminder: matching scores are not probabilities or proof of truth; review the evidence passages.")


if __name__ == "__main__":
    main()