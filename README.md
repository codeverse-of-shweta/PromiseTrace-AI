# PromiseTrace-AI
# 🔎 PromiseTrace AI — Track What Companies Actually Deliver

**PromiseTrace AI** is an AI-powered evidence tracking platform designed to connect public claims made by colleges, companies, and service providers with publicly available evidence.

It helps users understand what is supported by evidence, what remains unverified, and where evidence gaps exist — without making unsupported accusations.

## 🚀 Problem Statement

Organizations often make claims such as:
- “95% placement rate”
- “50+ industry partners”
- “Guaranteed internship opportunities”

Verifying these claims requires manually searching multiple websites, reports, press releases, and public documents. Claims can also change over time, making it difficult to track what was originally promised.

## 💡 Our Solution

PromiseTrace AI collects publicly documented claims, searches for relevant supporting evidence, and creates a traceable connection between each claim and its sources.

**Core workflow:**

`Claim → Source → Evidence → Gap Report`

## ✨ Key Features

- **Claim Extraction:** Capture claim text, source URLs, categories, and dates.
- **Evidence Mapping:** Connect claims with relevant public documents and announcements.
- **Verification Status:** Distinguish corroborated, partially supported, self-reported, unsupported-by-found evidence, and contradicted claims.
- **Evidence Trail:** Provide source links and supporting text for transparent review.
- **Evidence Gap Reports:** Highlight available evidence and what remains unverified.
- **Claim History:** Support tracking changes in claims over time.
- **Right of Reply:** Allow organizations to submit additional evidence for consideration.

## 🛠️ Tech Stack

The planned technology stack includes:

- **Frontend:** React, JavaScript, Tailwind CSS
- **UI & Charts:** Lucide React, Recharts
- **Web Research:** TinyFish API
- **AI Layer:** Large Language Model (LLM) for structured claim extraction and evidence matching
- **Backend:** Python (FastAPI) or Node.js
- **Database:** PostgreSQL
- **Data Sources:** Official websites, public reports, regulator portals, and news sources

*The final implementation may vary as development progresses.*

## 🎯 Target Users

- Students and parents researching colleges
- Procurement and vendor evaluation teams
- Investors and journalists
- Researchers and other users evaluating public claims

## 🧪 MVP Scope

Our initial focus is on private colleges, particularly claims related to placements and industry partnerships.

The MVP aims to demonstrate:
1. Claim collection from official sources
2. Public evidence retrieval
3. Claim-to-evidence mapping
4. A traceable evidence trail
5. An evidence gap report

## ⚖️ Responsible Verification

PromiseTrace AI is designed to distinguish between missing evidence and contradictory evidence.

**“No public evidence found” does not mean “false.”**

Each result should communicate its sources, limitations, and verification status transparently.

## 👥 Team — Team Levi

Developed as a hackathon project by students of Accurate Institute of Management and Technology.

- **Shweta Mishra** — Team Lead
- **Shivam Rajpoot** — AI / Backend
- **Anamika Tomar** — Frontend / Dashboard
- **Girish Kumar** — Research / Design

## 🔮 Future Scope

- Expand verification to companies and service providers
- Scheduled monitoring for changes in public claims
- Multilingual support
- Browser extension for claim checking
- API access for bulk evidence reports

## 📌 Project Status

Hackathon MVP — under development.

Features, integrations, and verification capabilities will evolve as implementation progresses.

---

*PromiseTrace AI — Public claims deserve transparent evidence.*
