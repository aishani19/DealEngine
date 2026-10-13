import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import ActionStatus

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["rag_chunks_loaded"] > 0


def test_chat_endpoint():
    response = client.post(
        "/api/chat",
        json={"message": "What AI services does Cynbit offer for high-concurrency systems?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 50
    assert len(data["citations"]) > 0
    assert data["latency_ms"] >= 0


def test_lead_qualify_and_proposal_pipeline():
    lead_payload = {
        "name": "Rajiv Mehra",
        "company": "Horizon Realty Partners",
        "email": "rajiv@horizonrealty.in",
        "role": "Managing Director",
        "budget_range": "$10,000 - $25,000",
        "timeline": "1 - 3 Months",
        "primary_interest": "TenantEase SaaS",
        "inquiry_text": "Need TenantEase customized for 1,200 tenants with WhatsApp payment reminders."
    }
    # 1. Qualify
    qual_res = client.post("/api/leads/qualify", json=lead_payload)
    assert qual_res.status_code == 200
    qual_data = qual_res.json()
    assert qual_data["total_fit_score"] >= 60

    # 2. Proposal
    prop_res = client.post("/api/proposals/generate", json=lead_payload)
    assert prop_res.status_code == 200
    prop_data = prop_res.json()
    assert len(prop_data["phased_roadmap"]) >= 1
    assert "drafted_response_email" in prop_data


def test_human_approval_lifecycle():
    # 1. Get pending
    pending_res = client.get("/api/actions/pending")
    assert pending_res.status_code == 200
    pending_list = pending_res.json()
    assert len(pending_list) > 0

    first_action_id = pending_list[0]["action_id"]

    # 2. Decision: Approve
    decision_payload = {
        "action_id": first_action_id,
        "approved": True,
        "reviewer_notes": "Reviewed by Senior Solutions Architect. Approved for delivery."
    }
    dec_res = client.post("/api/actions/decision", json=decision_payload)
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["status"] == ActionStatus.DISPATCHED.value
