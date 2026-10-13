import pytest
from backend.models import LeadInput, IntentTier
from backend.services.lead_scorer import LeadScorer


def test_enterprise_ai_lead_scoring():
    lead = LeadInput(
        name="Sarah Jenkins",
        company="Apex Logistics",
        email="s.jenkins@apexlogistics.com",
        role="VP of Technology",
        budget_range="$25,000 - $50,000",
        timeline="Immediate (Within 30 days)",
        primary_interest="AI Automation",
        inquiry_text="We need to build autonomous multi-agent dispatch workflows for 450 freight trucks."
    )
    score = LeadScorer.score_lead(lead)
    assert score.total_fit_score >= 80
    assert score.tier == IntentTier.TIER_1_ENTERPRISE
    assert "LangChain" in score.tech_stack_recommendation or "FastAPI" in score.tech_stack_recommendation


def test_unqualified_student_lead():
    lead = LeadInput(
        name="Tommy Lee",
        company="Student",
        email="tommy@gmail.com",
        role="Student",
        budget_range="< $500",
        timeline="tomorrow",
        primary_interest="General Inquiry",
        inquiry_text="Can you build free Instagram clone for my homework tomorrow?"
    )
    score = LeadScorer.score_lead(lead)
    assert score.total_fit_score < 40
    assert score.tier == IntentTier.TIER_4_UNQUALIFIED
    assert any("Budget Deficit" in f or "Commercial Fit" in f for f in score.risk_flags)
