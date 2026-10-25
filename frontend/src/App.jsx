import { useState } from "react";
import {
  ShieldCheck,
  Search,
  FileSearch,
  Activity,
  Globe,
  ArrowUpRight,
  CheckCircle2,
  AlertCircle,
  Clock3,
  ExternalLink,
  ChevronRight,
  Menu,
  X,
  Sparkles
} from "lucide-react";
import "./App.css";

const demoClaims = [
  {
    id: "PT-001",
    title: "Industry research collaborations",
    category: "Industry partnerships",
    status: "Partially supported",
    score: 78,
    source: "https://www.iisc.ac.in/",
    snippet:
      "Institutional research and industry engagement information is available on the official website.",
    year: "2025"
  },
  {
    id: "PT-002",
    title: "Career and internship opportunities",
    category: "Career opportunities",
    status: "Needs more evidence",
    score: null,
    source: "https://www.iisc.ac.in/",
    snippet:
      "Official institutional pages provide information about research, programmes and career opportunities. Independent evidence for the specific claim is still needed.",
    year: "2025"
  },
  {
    id: "PT-003",
    title: "Published placement statistics",
    category: "Placement statistics",
    status: "Needs more evidence",
    score: null,
    source: "https://www.iisc.ac.in/",
    snippet:
      "A specific, independently verifiable placement statistic has not been established in this demo.",
    year: "Not found"
  }
];

function normalizeStatus(status) {
  const value = String(status || "").toLowerCase();

  if (
    value.includes("contradicted") ||
    value.includes("conflicting")
  ) {
    return "Conflicting evidence";
  }

  if (
    value.includes("corroborated") ||
    value === "supported" ||
    value === "evidence found"
  ) {
    return "Supported by evidence";
  }

  if (
    value.includes("partial") ||
    value.includes("potentially supported")
  ) {
    return "Partially supported";
  }

  if (
    value.includes("no public evidence") ||
    value.includes("insufficient") ||
    value.includes("unavailable") ||
    value.includes("self-reported") ||
    value.includes("not independently verified")
  ) {
    return "Needs more evidence";
  }

  return status || "Not independently verified";
}

function statusClass(status) {
  if (status === "Supported by evidence") return "status-supported";
  if (status === "Partially supported") return "status-partial";
  if (status === "Conflicting evidence") return "status-contradicted";
  return "status-insufficient";
}

function App() {
  const [url, setUrl] = useState("");
  const [scannedUrl, setScannedUrl] = useState("");
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");
  const [claims, setClaims] = useState(demoClaims);
  const [demoMode, setDemoMode] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState("All claims");

  const normalizedClaims = claims.map((claim) => ({
    ...claim,
    status: normalizeStatus(claim.status)
  }));

  const supportedCount = normalizedClaims.filter(
    (claim) => claim.status === "Supported by evidence"
  ).length;

  const reviewCount = normalizedClaims.filter(
    (claim) => claim.status !== "Supported by evidence"
  ).length;

  const visibleClaims = normalizedClaims.filter((claim) => {
    if (activeFilter === "All claims") return true;
    if (activeFilter === "Supported") {
      return claim.status === "Supported by evidence";
    }
    if (activeFilter === "Needs review") {
      return claim.status !== "Supported by evidence";
    }
    return true;
  });

  async function handleScan(event) {
    event.preventDefault();
    setError("");

    let parsedUrl;

    try {
      const input = url.trim();
      parsedUrl = new URL(
        /^https?:\/\//i.test(input) ? input : `https://${input}`
      );
    } catch {
      setError("Please enter a valid institution website.");
      return;
    }

    if (
      !["http:", "https:"].includes(parsedUrl.protocol) ||
      !parsedUrl.hostname.includes(".")
    ) {
      setError("Please enter a valid HTTP or HTTPS website address.");
      return;
    }

    setUrl(parsedUrl.href);
    setScannedUrl(parsedUrl.href);
    setScanning(true);
    setClaims([]);
    setDemoMode(false);

    try {
      const baseUrl = (
        import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
      ).replace(/\/+$/, "");

      const response = await fetch(`${baseUrl}/scan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          url: parsedUrl.href
        })
      });

      if (!response.ok) {
        throw new Error(`The scan request failed with status ${response.status}.`);
      }

      const data = await response.json();

      if (data.status === "pending") {
        setError(
          "The backend received your request, but live claim collection is not ready yet."
        );
        return;
      }

      if (data.status === "failed") {
        throw new Error(data.message || "The institution scan failed.");
      }

      const receivedClaims = Array.isArray(data.claims) ? data.claims : [];

      setClaims(
        receivedClaims.map((claim, index) => ({
          id: claim.id || `PT-${String(index + 1).padStart(3, "0")}`,
          title: claim.claim_text || claim.title || "Untitled claim",
          category:
            claim.category || claim.claim_type || claim.type || "General",
          status: normalizeStatus(
            claim.status || claim.final_status || "Not independently verified"
          ),
          score: claim.matching_score ?? null,
          source:
            claim.source_url ||
            claim.page_url ||
            claim.best_evidence?.source_url ||
            parsedUrl.href,
          snippet:
            claim.evidence?.[0]?.snippet ||
            claim.best_evidence?.evidence_text ||
            claim.snippet ||
            "No supporting evidence snippet was returned.",
          year: claim.year_mentioned || "Not specified"
        }))
      );
    } catch (err) {
      setError(
        `${err.message} Check that the backend is running and allows requests from this frontend.`
      );
    } finally {
      setScanning(false);
    }
  }

  function loadExample() {
    setUrl("https://www.iisc.ac.in/");
    setError("");
    document.getElementById("scan")?.scrollIntoView({
      behavior: "smooth",
      block: "center"
    });
  }

  function scrollToSection(id) {
    setMenuOpen(false);
    document.getElementById(id)?.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">
            <ShieldCheck size={24} />
          </div>
          <div>
            <div className="brand-name">PromiseTrace</div>
            <div className="brand-caption">EVIDENCE INTELLIGENCE</div>
          </div>
          <button
            className="icon-button mobile-close"
            onClick={() => setMenuOpen(false)}
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>

        <div className="nav-label">MENU</div>

        <button
          className="nav-item active"
          onClick={() => scrollToSection("overview")}
        >
          <Activity size={18} />
          Overview
        </button>

        <button
          className="nav-item"
          onClick={() => scrollToSection("scan")}
        >
          <Search size={18} />
          Scan an institution
        </button>

        <button
          className="nav-item"
          onClick={() => scrollToSection("claims")}
        >
          <FileSearch size={18} />
          Review claims
        </button>

        <div className="sidebar-bottom">
          <div className="security-card">
            <div className="security-icon">
              <ShieldCheck size={20} />
            </div>
            <div className="security-title">Evidence over assumptions.</div>
            <p>
              Explore public claims, trace their sources and understand what
              the evidence actually supports.
            </p>
          </div>

          <div className="sidebar-footer">
            <span className="online-dot" />
            PromiseTrace AI
            <span className="version">v0.1</span>
          </div>
        </div>
      </aside>

      <main className="main-content" id="overview">
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            onClick={() => setMenuOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={22} />
          </button>

          <div className="breadcrumb">
            Home <ChevronRight size={15} /> <strong>Overview</strong>
          </div>

          <div className="topbar-right">
            <div className="avatar">PT</div>
          </div>
        </header>

        <section className="page-heading">
          <div>
            <div className="eyebrow">
              <Sparkles size={14} />
              PUBLIC CLAIMS. TRACEABLE EVIDENCE.
            </div>

            <h1>
              Promises deserve <span>proof.</span>
            </h1>

            <p>
              Explore institutional claims, examine their sources and discover
              what publicly available evidence supports them.
            </p>
          </div>
        </section>

        <section className="scan-panel" id="scan">
          <div className="scan-panel-heading">
            <div className="scan-icon">
              <Globe size={21} />
            </div>

            <div>
              <h2>What would you like to verify?</h2>
              <p>
                Enter an institution's official website to begin your review.
              </p>
            </div>
          </div>

          <form className="scan-form" onSubmit={handleScan}>
            <div className="input-wrap">
              <Globe size={18} />

              <input
                type="text"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                placeholder="Enter a website, e.g. www.iisc.ac.in"
                aria-label="Institution website URL"
              />
            </div>

            <button className="scan-button" type="submit" disabled={scanning}>
              {scanning ? (
                <span className="spinner" />
              ) : (
                <Search size={17} />
              )}
              {scanning ? "Scanning..." : "Scan institution"}
            </button>
          </form>

          <div className="scan-bottom">
            <div className="scan-hint">
              <ShieldCheck size={15} />
              Publicly accessible information only
            </div>

            <button className="example-button" onClick={loadExample} type="button">
              Try example: IISc Bengaluru
              <ArrowUpRight size={14} />
            </button>
          </div>

          {error && (
            <div className="error-banner" role="alert">
              <AlertCircle size={17} />
              <span>{error}</span>
            </div>
          )}
        </section>

        <section className="section-header">
          <div>
            <div className="eyebrow">YOUR INVESTIGATION</div>
            <h2>Evidence overview</h2>
            <p className="section-description">
              A quick summary of the claims and evidence reviewed.
            </p>
          </div>

          <div className={`mode-badge ${demoMode ? "demo-badge" : ""}`}>
            <span />
            {demoMode ? "DEMO PREVIEW" : "LIVE SCAN"}
          </div>
        </section>

        {demoMode && (
          <div className="demo-notice">
            <AlertCircle size={18} />
            <div>
              <strong>You're viewing example data</strong>
              <span>
                These sample claims and scores are illustrative only. They
                have not been verified as findings about IISc.
              </span>
            </div>
          </div>
        )}

        <section className="stats-grid">
          <button
            className={`stat-card ${activeFilter === "All claims" ? "stat-active" : ""}`}
            onClick={() => {
              setActiveFilter("All claims");
              scrollToSection("claims");
            }}
          >
            <div className="stat-top">
              <span>Total claims</span>
              <div className="stat-icon cyan">
                <FileSearch size={18} />
              </div>
            </div>
            <div className="stat-value">
              {String(normalizedClaims.length).padStart(2, "0")}
            </div>
            <div className="stat-foot">Claims returned by the scan</div>
          </button>

          <button
            className={`stat-card ${activeFilter === "Supported" ? "stat-active" : ""}`}
            onClick={() => {
              setActiveFilter("Supported");
              scrollToSection("claims");
            }}
          >
            <div className="stat-top">
              <span>Supported by evidence</span>
              <div className="stat-icon green">
                <CheckCircle2 size={18} />
              </div>
            </div>
            <div className="stat-value">
              {String(supportedCount).padStart(2, "0")}
            </div>
            <div className="stat-foot">Claims with a supporting status</div>
          </button>

          <button
            className={`stat-card ${activeFilter === "Needs review" ? "stat-active" : ""}`}
            onClick={() => {
              setActiveFilter("Needs review");
              scrollToSection("claims");
            }}
          >
            <div className="stat-top">
              <span>Need further review</span>
              <div className="stat-icon amber">
                <Clock3 size={18} />
              </div>
            </div>
            <div className="stat-value">
              {String(reviewCount).padStart(2, "0")}
            </div>
            <div className="stat-foot">Claims needing further assessment</div>
          </button>
        </section>

        <section className="claims-section" id="claims">
          <div className="claims-heading">
            <div>
              <h2>Claim review</h2>
              <p>Check each claim, its source and the available evidence.</p>
            </div>

            <div className="claims-count">
              {visibleClaims.length} CLAIMS
            </div>
          </div>

          <div className="filter-row">
            {["All claims", "Supported", "Needs review"].map((filter) => (
              <button
                key={filter}
                className={`filter-button ${activeFilter === filter ? "filter-active" : ""}`}
                onClick={() => setActiveFilter(filter)}
              >
                {filter}
              </button>
            ))}
          </div>

          <div className="institution-bar">
            <div className="institution-symbol">
              <Globe size={19} />
            </div>

            <div className="institution-details">
              <strong>Institution under review</strong>
              <span>{scannedUrl || "No institution scanned yet"}</span>
            </div>

            {scannedUrl && (
              <a
                href={scannedUrl}
                target="_blank"
                rel="noreferrer"
                className="external-link"
                aria-label="Open institution website"
              >
                <ExternalLink size={17} />
              </a>
            )}
          </div>

          {scanning ? (
            <div className="empty-state">
              <span className="large-spinner" />
              <h3>Reviewing public information</h3>
              <p>
                The scan is running. It may take some time to collect and
                process evidence.
              </p>
            </div>
          ) : visibleClaims.length === 0 ? (
            <div className="empty-state">
              <FileSearch size={30} />
              <h3>No claims to display</h3>
              <p>
                No claims match this filter. Try another filter or scan an
                institution.
              </p>
              <button
                className="secondary-button"
                onClick={() => setActiveFilter("All claims")}
              >
                Show all claims
              </button>
            </div>
          ) : (
            <div className="claims-list">
              {visibleClaims.map((claim) => (
                <article className="claim-card" key={claim.id}>
                  <div className="claim-card-top">
                    <span className="claim-id">{claim.id}</span>
                    <span
                      className={`status-pill ${statusClass(claim.status)}`}
                    >
                      <span />
                      {claim.status}
                    </span>
                  </div>

                  <h3>{claim.title}</h3>

                  <div className="claim-category">
                    {claim.category}
                    <span>·</span>
                    {claim.year}
                  </div>

                  <div className="evidence-box">
                    <div className="evidence-heading">
                      <ShieldCheck size={15} />
                      AVAILABLE EVIDENCE
                    </div>

                    <p>{claim.snippet}</p>

                    <a
                      href={claim.source}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <ExternalLink size={13} />
                      View source
                      <ArrowUpRight size={13} />
                    </a>
                  </div>

                  {claim.score !== null &&
                    claim.score !== undefined &&
                    !demoMode && (
                      <div className="score-row">
                        <span>Text similarity score</span>
                        <strong>
                          {Math.round(
                            Number(claim.score) <= 1
                              ? Number(claim.score) * 100
                              : Number(claim.score)
                          )}
                          %
                        </strong>
                      </div>
                    )}

                  {demoMode && claim.score !== null && (
                    <div className="score-row">
                      <span>Example text similarity</span>
                      <strong>{claim.score}%</strong>
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>

        <footer className="page-footer">
          <div>
            <ShieldCheck size={17} />
            <strong>PromiseTrace AI</strong>
            <span>·</span>
            Evidence before conclusions.
          </div>

          <p>
            No public evidence found does not automatically mean a claim is
            false.
          </p>
        </footer>
      </main>
    </div>
  );
}

export default App;