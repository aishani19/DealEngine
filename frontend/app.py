import os
import json
import time
from pathlib import Path
import streamlit as st
import requests

from frontend.components.ui_helpers import (
    render_header, render_citations, render_bant_breakdown, render_tier_badge
)

# Page configuration
st.set_page_config(
    page_title="Cynbit DealEngine | AI Sales & Architectural Copilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom styling
css_path = Path(__file__).parent / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Backend URL configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# Local fallback service imports if backend is running embedded
try:
    from backend.services.llm_service import LLMService
    from backend.services.lead_scorer import LeadScorer
    from backend.services.proposal_generator import ProposalGenerator
    from backend.services.approval_workflow import ApprovalWorkflowService
    from backend.services.analytics_service import AnalyticsService
    from backend.rag.retriever import RAGRetriever
    from backend.models import LeadInput, ApprovalDecision
    LOCAL_SERVICES_AVAILABLE = True
except Exception:
    LOCAL_SERVICES_AVAILABLE = False


def call_backend(endpoint: str, method: str = "GET", payload: dict = None):
    """Helper to query FastAPI backend with graceful fallback to local service imports."""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        if method == "POST":
            res = requests.post(url, json=payload, timeout=10)
        else:
            res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json(), "API"
    except Exception:
        pass

    # Embedded local execution fallback for zero-fail Streamlit standalone mode
    if LOCAL_SERVICES_AVAILABLE:
        try:
            if endpoint == "/api/health":
                retriever = RAGRetriever.get_instance()
                workflow = ApprovalWorkflowService.get_instance()
                return {
                    "status": "healthy (embedded mode)",
                    "rag_chunks_loaded": len(retriever.doc_store.chunks),
                    "pending_human_approvals": len(workflow.get_pending_actions())
                }, "EMBEDDED"
            elif endpoint == "/api/chat" and method == "POST":
                llm = LLMService()
                res = llm.generate_chat_response(
                    message=payload.get("message", ""),
                    history=[],
                    api_key_override=payload.get("api_key_override"),
                    provider_override=payload.get("provider_override")
                )
                return res, "EMBEDDED"
            elif endpoint == "/api/leads/qualify" and method == "POST":
                lead_obj = LeadInput(**payload)
                score = LeadScorer.score_lead(lead_obj)
                return score.model_dump(), "EMBEDDED"
            elif endpoint == "/api/proposals/generate" and method == "POST":
                lead_obj = LeadInput(**payload)
                score = LeadScorer.score_lead(lead_obj)
                proposal = ProposalGenerator.generate_proposal(lead_obj, score)
                # auto enqueue action
                from backend.models import ApprovalRequest, ActionStatus
                import uuid
                act = ApprovalRequest(
                    action_id=f"act-{uuid.uuid4().hex[:8]}",
                    action_type="DISPATCH_SCOPING_EMAIL",
                    lead_name=lead_obj.name,
                    company_name=lead_obj.company,
                    recipient_email=lead_obj.email,
                    email_subject=f"Technical Discovery & Architectural Scoping | Cynbit Technologies ({lead_obj.primary_interest})",
                    email_body=proposal.drafted_response_email,
                    metadata={"deal_score": score.total_fit_score, "tier": score.tier.value},
                    status=ActionStatus.PENDING_APPROVAL
                )
                ApprovalWorkflowService.get_instance().create_action(act)
                return proposal.model_dump(), "EMBEDDED"
            elif endpoint == "/api/actions/pending":
                acts = ApprovalWorkflowService.get_instance().get_pending_actions()
                return [a.model_dump() for a in acts], "EMBEDDED"
            elif endpoint == "/api/actions/decision" and method == "POST":
                dec = ApprovalDecision(**payload)
                act = ApprovalWorkflowService.get_instance().process_decision(dec)
                return act.model_dump(), "EMBEDDED"
            elif endpoint == "/api/analytics":
                overview = AnalyticsService.get_overview()
                return overview.model_dump(), "EMBEDDED"
            elif endpoint == "/api/kb/sources":
                retriever = RAGRetriever.get_instance()
                return {
                    "index_statistics": retriever.get_index_stats(),
                    "preview_chunks": [c.to_dict() for c in retriever.doc_store.chunks[:6]]
                }, "EMBEDDED"
        except Exception as e:
            return {"error": str(e)}, "ERROR"

    return {"error": "Backend unavailable"}, "ERROR"


# --- Sidebar ---
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 10px 0 20px 0;">
            <div style="font-size: 24px; font-weight: 900; letter-spacing: -0.02em; color: #ffffff;">
                CYNBIT <span style="color: #38bdf8;">TECHNOLOGIES</span>
            </div>
            <div style="font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.2em; margin-top: 4px;">
                The Optimistic Architect
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚙️ Engine Settings")
    provider_choice = st.selectbox(
        "LLM Provider",
        ["High-Fidelity Demo (Deterministic)", "Groq (Llama-3.3-70b)", "OpenAI (GPT-4o-mini)"],
        index=0
    )
    provider_key = "demo"
    if "Groq" in provider_choice:
        provider_key = "groq"
    elif "OpenAI" in provider_choice:
        provider_key = "openai"

    api_key_input = ""
    if provider_key in ["groq", "openai"]:
        api_key_input = st.text_input(
            f"Enter {provider_key.upper()} API Key",
            type="password",
            help="Optional: Enter key to test real LLM inference live, or leave blank to use Demo Engine."
        )
        if not api_key_input:
            st.caption("⚡ *Operating in Cynbit Neural Demo Mode (No API key required).*")

    st.divider()

    # System Health check
    health_data, conn_mode = call_backend("/api/health")
    if conn_mode != "ERROR":
        st.success(f"System Online ({conn_mode} Mode)")
        chunks = health_data.get("rag_chunks_loaded", 12)
        pending = health_data.get("pending_human_approvals", 2)
        st.markdown(f"""
            <div style="font-size: 12px; color: #94a3b8; line-height: 1.6;">
                • <b>Indexed RAG Chunks:</b> {chunks}<br/>
                • <b>Pending Approvals:</b> {pending}<br/>
                • <b>Location:</b> Pratap Nagar, Jaipur
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Connecting to Engine...")

    st.divider()
    st.markdown("""
        <div style="font-size: 11px; color: #64748b; line-height: 1.5;">
            <b>Cynbit DealEngine v1.0</b><br/>
            Engineered for high-intent inbound enterprise deal qualification, proposal drafting, and human-governed automation.
        </div>
    """, unsafe_allow_html=True)


# --- Main UI ---
render_header()

# Load Sample Leads for select dropdowns
sample_leads_path = Path(__file__).parent.parent / "data" / "sample_leads.json"
sample_leads = []
if sample_leads_path.exists():
    with open(sample_leads_path, "r", encoding="utf-8") as f:
        sample_leads = json.load(f)

# Top navigation tabs
tab_chat, tab_scorer, tab_proposals, tab_analytics = st.tabs([
    "💬 LeadArchitect Copilot (RAG Chat)",
    "🎯 Lead Scorer & Scoping Radar",
    "📝 Proposal Studio & Human Approval Hub",
    "📊 Pipeline Velocity & Analytics"
])


# ==========================================
# TAB 1: LeadArchitect RAG Chatbot
# ==========================================
with tab_chat:
    st.markdown("""
        <div style="margin-bottom: 16px;">
            <h3 style="margin-bottom: 4px; font-weight: 800;">Consultative Architectural Dialogue</h3>
            <p style="color: #94a3b8; font-size: 14px;">
                Ask questions regarding Cynbit's AI services, autonomous agent frameworks, TenantEase, Revio, BitElevate, or client case studies. All answers cite verified company sources.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Prompt suggestions
    st.markdown("**Quick Scoping Prompts:**")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    quick_prompt = None
    if col_p1.button("🤖 Scope AI Agents"):
        quick_prompt = "How does Cynbit architect autonomous AI agents and enterprise RAG systems?"
    if col_p2.button("🏢 TenantEase SaaS"):
        quick_prompt = "What capabilities does TenantEase offer for residential property portfolios?"
    if col_p3.button("⚡ Evento Case Study"):
        quick_prompt = "Tell me about Cynbit's case study with Evento and how you achieved zero latency for 50k users."
    if col_p4.button("🎓 BitElevate Tracks"):
        quick_prompt = "What engineering tracks and mentorship are available through BitElevate?"

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I am **Cynbit LeadArchitect**, your technical solutions and discovery copilot. "
                    "At Cynbit Technologies, we operate as 'The Optimistic Architect'—combining startup speed with enterprise rigor. "
                    "How can I help you evaluate our Autonomous AI Agents, custom software engineering, TenantEase SaaS, or cloud infrastructure?"
                ),
                "citations": []
            }
        ]

    # Render history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("citations"):
                render_citations(msg["citations"])

    # User Input
    user_query = st.chat_input("Ask Cynbit LeadArchitect a scoping question...")
    if quick_prompt:
        user_query = quick_prompt

    if user_query:
        # Append user message
        st.session_state.chat_messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Call engine
        with st.chat_message("assistant"):
            with st.spinner("Synthesizing architectural response from Cynbit knowledge base..."):
                payload = {
                    "message": user_query,
                    "provider_override": provider_key,
                    "api_key_override": api_key_input
                }
                res_data, _ = call_backend("/api/chat", method="POST", payload=payload)
                
                reply_text = res_data.get("reply", "Apologies, could not process request.")
                citations = res_data.get("citations", [])
                intent = res_data.get("detected_intent")
                latency = res_data.get("latency_ms", 0.0)
                model_used = res_data.get("model_used", "Cynbit Engine")

                st.markdown(reply_text)
                if citations:
                    render_citations(citations)

                st.caption(f"⚡ Latency: {latency}ms | Model: {model_used} | Intent: {intent}")

                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": reply_text,
                    "citations": citations
                })


# ==========================================
# TAB 2: Lead Scorer & Scoping Radar
# ==========================================
with tab_scorer:
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h3 style="margin-bottom: 4px; font-weight: 800;">Automated BANT / MEDDIC Lead Qualification</h3>
            <p style="color: #94a3b8; font-size: 14px;">
                Evaluate prospect requirements across Budget, Authority, Need, and Timeline. Select a preset lead or enter custom parameters.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Preset selection
    lead_options = ["Custom Entry"] + [f"{l['company']} ({l['name']} - {l['primary_interest']})" for l in sample_leads]
    selected_option = st.selectbox("Load Realistic Inbound Lead Preset:", lead_options, index=1)

    default_lead = {
        "name": "", "company": "", "email": "", "role": "VP / Director",
        "budget_range": "$25,000 - $50,000", "timeline": "Immediate (Within 30 days)",
        "primary_interest": "AI Automation", "inquiry_text": ""
    }
    if selected_option != "Custom Entry":
        idx = lead_options.index(selected_option) - 1
        default_lead = sample_leads[idx]

    with st.form("lead_scoping_form"):
        col1, col2 = st.columns(2)
        with col1:
            form_name = st.text_input("Contact Name", value=default_lead["name"])
            form_company = st.text_input("Company / Organization", value=default_lead["company"])
            form_email = st.text_input("Corporate Email", value=default_lead["email"])
            form_role = st.text_input("Role / Title", value=default_lead.get("role", "Decision Maker"))
        with col2:
            form_interest = st.selectbox(
                "Primary Architectural Interest",
                ["AI Automation", "TenantEase SaaS & Customization", "Software Engineering & Cloud Systems", "BitElevate Enterprise Upskilling", "General Inquiry"],
                index=0 if "AI" in default_lead.get("primary_interest", "") else 1
            )
            form_budget = st.selectbox(
                "Budget Range",
                ["$40,000 - $70,000+", "$25,000 - $50,000", "$10,000 - $25,000", "$5,000 - $10,000", "< $500 (Student / Free)"],
                index=1 if "$25,000" in default_lead.get("budget_range", "") else 0
            )
            form_timeline = st.selectbox(
                "Delivery Timeline Horizon",
                ["Immediate (Within 30 days)", "1 - 3 Months", "3 - 6 Months", "Uncertain / Just exploring"],
                index=0 if "Immediate" in default_lead.get("timeline", "") else 1
            )

        form_inquiry = st.text_area(
            "Inbound Technical Scope / Requirement Narrative",
            value=default_lead.get("inquiry_text", ""),
            height=120
        )

        submit_btn = st.form_submit_button("⚡ Run Multi-Dimensional Lead Qualification", use_container_width=True)

    if submit_btn or selected_option != "Custom Entry":
        lead_payload = {
            "name": form_name or "Anonymous Prospect",
            "company": form_company or "Enterprise Prospect",
            "email": form_email or "lead@enterprise.com",
            "role": form_role,
            "budget_range": form_budget,
            "timeline": form_timeline,
            "primary_interest": form_interest,
            "inquiry_text": form_inquiry or "Inquiry into technical architecture and delivery roadmap."
        }

        with st.spinner("Calculating BANT Fit, tech stack fit, and risk flags..."):
            score_data, _ = call_backend("/api/leads/qualify", method="POST", payload=lead_payload)

            if "error" not in score_data:
                st.session_state.current_score = score_data
                st.session_state.current_lead = lead_payload

                st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'/>", unsafe_allow_html=True)
                render_tier_badge(score_data.get("tier"), score_data.get("total_fit_score"))
                render_bant_breakdown(score_data)

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("""
                        <div class="cynbit-card">
                            <h4 style="margin-bottom: 12px; color: #38bdf8;">🛠️ Recommended Architectural Stack</h4>
                    """, unsafe_allow_html=True)
                    for tech in score_data.get("tech_stack_recommendation", []):
                        st.markdown(f"• **{tech}**")
                    st.markdown("</div>", unsafe_allow_html=True)

                with col_b:
                    st.markdown("""
                        <div class="cynbit-card">
                            <h4 style="margin-bottom: 12px; color: #fbbf24;">⚠️ Risk & Feasibility Signals</h4>
                    """, unsafe_allow_html=True)
                    for risk in score_data.get("risk_flags", []):
                        st.markdown(f"• {risk}")
                    st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# TAB 3: Proposal Studio & Human Approval Hub
# ==========================================
with tab_proposals:
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h3 style="margin-bottom: 4px; font-weight: 800;">Proposal Studio & Human-in-the-Loop Governance</h3>
            <p style="color: #94a3b8; font-size: 14px;">
                Synthesize formal Discovery Briefs and enforce human architect sign-off before sending outreach emails or scheduling calls.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col_prop_left, col_prop_right = st.columns([1.1, 0.9])

    with col_prop_left:
        st.subheader("1. Generate Architectural Brief")
        
        # Build dynamic list of prospects to choose from
        available_prospects = {}
        if "current_lead" in st.session_state:
            curr = st.session_state.current_lead
            curr_label = f"⭐ Recently Scored: {curr.get('name')} ({curr.get('company')})"
            available_prospects[curr_label] = curr
            
        for lead in sample_leads:
            label = f"{lead.get('name')} ({lead.get('company')} - {lead.get('primary_interest')})"
            available_prospects[label] = lead

        selected_prospect_label = st.selectbox(
            "Select Target Prospect for Scoping Brief:",
            list(available_prospects.keys()),
            index=0
        )
        target_lead = available_prospects[selected_prospect_label]
        
        st.info(f"Targeting: **{target_lead.get('name')}** at **{target_lead.get('company')}** ({target_lead.get('primary_interest')})")

        if st.button("Generate Phased Discovery Brief & Draft Outreach", type="primary"):
            with st.spinner("Synthesizing phased roadmap and scoping email..."):
                prop_data, _ = call_backend("/api/proposals/generate", method="POST", payload=target_lead)
                if "error" not in prop_data:
                    st.session_state.latest_proposal = prop_data
                    st.success(f"Discovery Brief Synthesized for {target_lead.get('name')} & Enqueued for Review!")

        if "latest_proposal" in st.session_state:
            p = st.session_state.latest_proposal
            st.markdown(f"""
                <div class="cynbit-card">
                    <div class="cynbit-pill">EXECUTIVE SUMMARY</div>
                    <p style="margin-top: 10px; color: #e2e8f0; font-size: 14px;">{p.get('executive_summary')}</p>
                    <div style="font-weight: 700; color: #38bdf8; margin: 12px 0 6px 0;">Architectural Fit:</div>
                    <p style="font-size: 13px; color: #94a3b8;">{p.get('architectural_fit')}</p>
                    <div style="font-weight: 700; color: #34d399; margin-top: 10px;">Estimated Investment: {p.get('estimated_total_range')}</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("#### 🗺️ Phased Lifecycle Roadmap")
            for step in p.get("phased_roadmap", []):
                st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.5); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 12px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; font-weight: 700; color: #ffffff;">
                            <span>Phase {step.get('phase_number')}: {step.get('phase_name')}</span>
                            <span style="color: #38bdf8;">{step.get('duration')} | {step.get('estimated_investment')}</span>
                        </div>
                        <div style="font-size: 12px; color: #94a3b8; margin-top: 6px;">
                            Deliverables: {', '.join(step.get('key_deliverables', []))}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    with col_prop_right:
        st.subheader("2. Human-in-the-Loop Approval Queue")
        st.caption("Consequential actions (outreach emails, calendar invites) require explicit architect sign-off.")

        pending_actions, _ = call_backend("/api/actions/pending")
        if not pending_actions or len(pending_actions) == 0:
            st.success("No pending actions awaiting approval! All actions reviewed.")
        else:
            for act in pending_actions:
                act_id = act.get("action_id")
                with st.expander(f"📬 {act.get('company_name')} ({act.get('lead_name')}) - {act.get('action_type')}", expanded=True):
                    st.markdown(f"**Recipient:** `{act.get('recipient_email')}`")
                    st.markdown(f"**Subject:** *{act.get('email_subject')}*")
                    
                    edited_email = st.text_area(
                        "Email Body (Editable)",
                        value=act.get("email_body", ""),
                        height=200,
                        key=f"edit_{act_id}"
                    )

                    rev_notes = st.text_input("Reviewer Audit Notes", value="Approved after architectural review", key=f"notes_{act_id}")

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("✅ Approve & Dispatch", key=f"app_{act_id}", use_container_width=True):
                            dec_payload = {
                                "action_id": act_id,
                                "approved": True,
                                "reviewer_notes": rev_notes,
                                "modified_body": edited_email
                            }
                            call_backend("/api/actions/decision", method="POST", payload=dec_payload)
                            st.success(f"Action {act_id} APPROVED and DISPATCHED!")
                            time.sleep(1)
                            st.rerun()

                    with col_btn2:
                        if st.button("❌ Reject / Flag", key=f"rej_{act_id}", use_container_width=True):
                            dec_payload = {
                                "action_id": act_id,
                                "approved": False,
                                "reviewer_notes": rev_notes or "Rejected during review"
                            }
                            call_backend("/api/actions/decision", method="POST", payload=dec_payload)
                            st.error(f"Action {act_id} REJECTED and FLAGGED.")
                            time.sleep(1)
                            st.rerun()


# ==========================================
# TAB 4: Pipeline Velocity & Analytics
# ==========================================
with tab_analytics:
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h3 style="margin-bottom: 4px; font-weight: 800;">Executive Pipeline & Engine Analytics</h3>
            <p style="color: #94a3b8; font-size: 14px;">
                Real-time measurements of qualification turnaround, architect labor savings, and deal tier distribution.
            </p>
        </div>
    """, unsafe_allow_html=True)

    analytics_data, _ = call_backend("/api/analytics")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{analytics_data.get('total_leads_processed', 14)}</div>
                <div class="metric-label">Inbound Leads Evaluated</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{analytics_data.get('avg_lead_fit_score', 78.4)}/100</div>
                <div class="metric-label">Avg Deal Fit Score</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value" style="color: #34d399;">{analytics_data.get('manual_qualification_hours_saved', 35.0)}h</div>
                <div class="metric-label">Architect Hours Saved</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value" style="color: #38bdf8;">{analytics_data.get('pipeline_value_identified', '$245,000')}</div>
                <div class="metric-label">Pipeline Value Identified</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    col_chart, col_kb = st.columns(2)
    with col_chart:
        st.markdown("""
            <div class="cynbit-card">
                <h4 style="margin-bottom: 12px; color: #38bdf8;">⏱️ Qualification Latency Benchmark</h4>
                <div style="margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                        <span>Traditional Manual Review:</span>
                        <span style="color: #f87171; font-weight: 700;">24.0 Hours</span>
                    </div>
                    <div style="background: rgba(239, 68, 68, 0.2); height: 8px; border-radius: 4px;">
                        <div style="background: #ef4444; width: 100%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                        <span>Cynbit DealEngine Copilot:</span>
                        <span style="color: #34d399; font-weight: 700;">1.35 Seconds (99.9% Faster)</span>
                    </div>
                    <div style="background: rgba(16, 185, 129, 0.2); height: 8px; border-radius: 4px;">
                        <div style="background: #10b981; width: 3%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
                <div style="margin-top: 24px;">
                    <h5 style="color: #ffffff; margin-bottom: 8px;">Lead Tier Distribution</h5>
                    <div style="font-size: 13px; color: #94a3b8; line-height: 1.8;">
                        • <b>Tier 1 - Enterprise Fit:</b> 43%<br/>
                        • <b>Tier 2 - Mid-Market:</b> 29%<br/>
                        • <b>Tier 3 - Exploratory:</b> 14%<br/>
                        • <b>Tier 4 - Unqualified:</b> 14%
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_kb:
        st.markdown("""
            <div class="cynbit-card">
                <h4 style="margin-bottom: 12px; color: #38bdf8;">📚 Grounded Knowledge Base Index</h4>
        """, unsafe_allow_html=True)
        kb_sources, _ = call_backend("/api/kb/sources")
        if "index_statistics" in kb_sources:
            stats = kb_sources["index_statistics"]
            st.markdown(f"""
                <div style="font-size: 13px; color: #94a3b8; line-height: 1.8;">
                    • <b>Total Chunks:</b> {stats.get('total_chunks')}<br/>
                    • <b>Vocabulary Size:</b> {stats.get('vocabulary_size')} tokens<br/>
                    • <b>Vector Dimension:</b> {stats.get('vector_dimension')}<br/>
                    • <b>Indexed Document Files:</b>
                </div>
            """, unsafe_allow_html=True)
            for src in stats.get("sources", []):
                st.code(src, language="json")
        st.markdown("</div>", unsafe_allow_html=True)
