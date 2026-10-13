import streamlit as st
from typing import List, Dict, Any


def render_header():
    st.markdown("""
        <div style="padding: 18px 0 24px 0; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <div class="cynbit-pill">CYNBIT TECHNOLOGIES • JAIPUR, INDIA</div>
                    <h1 style="font-size: 32px; font-weight: 900; margin: 10px 0 4px 0; letter-spacing: -0.03em; color: #ffffff;">
                        DealEngine <span style="background: linear-gradient(135deg, #38bdf8 0%, #6366f1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Copilot</span>
                    </h1>
                    <p style="color: #94a3b8; font-size: 15px; margin: 0;">
                        Autonomous Inbound Lead Qualification, Architectural Scoping & Sales Intelligence Engine
                    </p>
                </div>
                <div style="text-align: right;">
                    <span class="cynbit-pill success">● Production Engine Live</span>
                    <div style="font-size: 11px; color: #64748b; margin-top: 6px;">The Optimistic Architect</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_citations(citations: List[Dict[str, Any]]):
    if not citations:
        return
    with st.expander(f"📚 Grounded Knowledge Sources & Citations ({len(citations)})", expanded=False):
        for i, c in enumerate(citations):
            score = c.get("relevance_score", 0.0)
            score_pct = int(score * 100)
            st.markdown(f"""
                <div class="citation-box">
                    <div style="display: flex; justify-content: space-between; font-weight: 700; color: #38bdf8; margin-bottom: 4px;">
                        <span>[{i+1}] {c.get('source_title')}</span>
                        <span>Relevance: {score_pct}%</span>
                    </div>
                    <div style="font-size: 11px; color: #94a3b8; margin-bottom: 6px;">
                        Section: {c.get('section')} | File: <code>{c.get('source_file')}</code>
                    </div>
                    <div style="font-style: italic; color: #e2e8f0; font-size: 12px; line-height: 1.4;">
                        "{c.get('snippet')}"
                    </div>
                </div>
            """, unsafe_allow_html=True)


def render_bant_breakdown(score_data: Dict[str, Any]):
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{score_data.get('budget_score')}/25</div>
                <div class="metric-label">Budget Fit</div>
            </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{score_data.get('authority_score')}/25</div>
                <div class="metric-label">Authority Level</div>
            </div>
        """, unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{score_data.get('need_score')}/25</div>
                <div class="metric-label">Technical Need</div>
            </div>
        """, unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{score_data.get('timeline_score')}/25</div>
                <div class="metric-label">Timeline Urgency</div>
            </div>
        """, unsafe_allow_html=True)


def render_tier_badge(tier_str: str, total_score: int):
    color_class = "success" if total_score >= 80 else ("warning" if total_score >= 60 else "danger")
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin: 12px 0;">
            <div class="cynbit-pill {color_class}" style="font-size: 13px; padding: 8px 16px;">
                {tier_str}
            </div>
            <div style="font-size: 20px; font-weight: 800; color: #ffffff;">
                Overall Deal Fit: <span style="color: #38bdf8;">{total_score}/100</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
