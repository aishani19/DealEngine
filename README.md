# Cynbit DealEngine Copilot ⚡
**Autonomous Inbound Lead Qualification, Architectural Scoping & Sales Intelligence Engine**

> Built for **Cynbit Technologies** (Jaipur, Rajasthan, India)  
> Brand Positioning: *"The Optimistic Architect — Architecting the future with AI automation"*  
> Reference: [https://www.cynbit.in/](https://www.cynbit.in/)

---

## 🌟 Overview & Business Impact

**Cynbit DealEngine** is an enterprise-grade AI copilot designed to solve Cynbit's primary top-of-funnel operational bottleneck: **manual, high-latency technical lead qualification and proposal drafting**.

Instead of senior solutions architects spending 3.5 hours per inbound inquiry parsing project scope and drafting exploratory proposals, DealEngine provides:
1. **Interactive Prospect Discovery Agent:** Multi-turn consultative conversational agent grounded in Cynbit's factual service domains, SaaS products (`TenantEase`, `Revio`, `Cynbit Studio`), educational tracks (`BitElevate`), and case studies (`Evento`, `Marketing Addict`).
2. **Algorithmic BANT / MEDDIC Lead Qualification:** Evaluates budget, authority, need, and timeline to calculate an objective **Deal Fit Score (0–100)** and assign actionable intent tiers.
3. **Architectural Discovery Brief & Phased Roadmap:** Generates a 3-phase technical implementation plan mapped to Cynbit's 6-step lifecycle and drafts a personalized client proposal email.
4. **Human-in-the-Loop Governance:** Puts all consequential actions (sending outreach emails, booking discovery calls) into a secure approval queue where a human architect can review, edit, and approve or reject with one click.
5. **Executive Pipeline Dashboard:** Real-time visibility into pipeline velocity, qualification turnaround (1.35s vs. 24h manual), and labor savings.

---

## 📂 Project Structure

```
Cynbit_Submission/
├── AI_OPPORTUNITY_REPORT.md             # Complete Business Case & Strategic ROI Report
├── TECHNICAL_APPROACH_REPORT.md         # In-Depth Technical Architecture & Benchmark Report
├── README.md                            # Complete Setup, Architecture & Operation Guide
├── requirements.txt                     # Production Python Dependencies
├── .env.example                         # Environment Configuration Template
├── .gitignore                           # Git ignore rules for secrets and build artifacts
├── data/
│   ├── knowledge_base/                  # Grounded Company Documents (Cynbit.in)
│   │   ├── cynbit_overview.json         # Company Profile, Archetype & Locations
│   │   ├── cynbit_services.json         # AI Agents, Full-Stack Dev, Cloud, Technical SEO
│   │   ├── cynbit_products.json         # TenantEase, Revio, Cynbit Studio
│   │   ├── cynbit_bitelevate.json       # BitElevate Mentorship & Engineering Tracks
│   │   ├── cynbit_case_studies.json     # Evento (50k users), Marketing Addict, etc.
│   │   └── cynbit_lifecycle_pricing.json# 6-Step Lifecycle & Sprint Investment Tiers
│   └── sample_leads.json                # Realistic Inbound Lead Test Cases
├── backend/
│   ├── main.py                          # FastAPI Application with REST Endpoints & CORS
│   ├── config.py                        # Settings and Environment Loader
│   ├── models.py                        # Pydantic Schemas for Requests, Leads & Approvals
│   ├── rag/
│   │   ├── document_store.py            # Knowledge Ingestion & Semantic Chunking
│   │   └── retriever.py                 # Vector Space Index & Cosine Similarity Retriever
│   ├── services/
│   │   ├── llm_service.py               # Real LLM (Groq/OpenAI) + Deterministic Demo Engine
│   │   ├── lead_scorer.py               # BANT Lead Scoring & Tech Stack Classifier
│   │   ├── proposal_generator.py        # Discovery Brief & Phased Roadmap Generator
│   │   ├── approval_workflow.py         # Human-in-the-Loop State Machine & Audit Log
│   │   └── analytics_service.py         # Pipeline KPIs & Telemetry Tracker
│   └── utils/
│       └── guardrails.py                # Injection Defense, PII Masking & Topic Filter
├── frontend/
│   ├── app.py                           # Premium Streamlit UI with Cynbit Brand Aesthetics
│   ├── styles.css                       # Modern Glassmorphic Stylesheet & Dark Mode
│   └── components/
│       └── ui_helpers.py                # Reusable UI Metrics, Badges & Citation Expanders
└── tests/
    ├── test_api.py                      # FastAPI REST Endpoint Integration Tests
    ├── test_rag.py                      # RAG Document Store & Vector Search Tests
    └── test_lead_scorer.py              # BANT Scoring Algorithm Validation Tests
```

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12 installed.

### 2. Install Dependencies
```bash
cd "c:\Users\aishani billore\OneDrive\Desktop\Cynbit_Submission"
pip install -r requirements.txt
```

### 3. Configure Environment (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*Note: The prototype includes a **Deterministic High-Fidelity Demo Simulation Engine**. If no API keys are provided, all RAG citations, scoring engines, proposal generators, and approval queues function smoothly without errors. To enable live inference, provide `GROQ_API_KEY` or `OPENAI_API_KEY` in `.env` or in the Streamlit UI sidebar.*

---

## 🏃 Running the Application

### Option A: Standard Full-Stack Execution (FastAPI + Streamlit)
Open two terminal windows:

**Terminal 1 — FastAPI Backend:**
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`*

**Terminal 2 — Streamlit Frontend UI:**
```bash
python -m streamlit run frontend/app.py --server.port 8501
```
*Interactive Frontend: `http://localhost:8501`*

### Option B: Standalone Resilient Streamlit Execution
The Streamlit frontend includes built-in embedded backend service fallbacks. You can run:
```bash
python -m streamlit run frontend/app.py
```
*The app automatically detects if the FastAPI server is running; if not, it runs the backend services embedded in-process so you can test all features with zero friction.*

---

## 🧪 Running Automated Tests

Run the complete test suite with `pytest`:
```bash
python -m pytest tests -v
```

All 9 integration and unit tests validate:
- RAG document chunk ingestion and vector retrieval
- Source citation generation and grounding precision
- BANT lead scoring across Enterprise vs. Unqualified inputs
- FastAPI endpoint health, chat, qualification, and proposal endpoints
- Human-in-the-loop state transitions (`PENDING_APPROVAL` ➔ `DISPATCHED` / `REJECTED`)

---

## 📊 Key Business & Technical Deliverables

1. [AI Opportunity Report](file:///c:/Users/aishani%20billore/OneDrive/Desktop/Cynbit_Submission/AI_OPPORTUNITY_REPORT.md): In-depth business analysis, problem identification, target personas, financial ROI model, model selection rationale, and pipeline architecture.
2. [Technical Approach Report](file:///c:/Users/aishani%20billore/OneDrive/Desktop/Cynbit_Submission/TECHNICAL_APPROACH_REPORT.md): System architecture diagrams, vector embeddings strategy, prompt guardrails, evaluation benchmarks, and zero-trust cloud deployment instructions.
3. [FastAPI Backend Service](file:///c:/Users/aishani%20billore/OneDrive/Desktop/Cynbit_Submission/backend/main.py): Production REST API with RAG retrieval, lead scoring, proposal drafting, and human approval state machine.
4. [Streamlit Production UI](file:///c:/Users/aishani%20billore/OneDrive/Desktop/Cynbit_Submission/frontend/app.py): Polished dark-mode interface styled to match Cynbit's modern brand guidelines.
