import logging
import uuid
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.models import (
    ChatRequest, ChatResponse,
    LeadInput, BantScore, ProposalBrief,
    ApprovalRequest, ApprovalDecision, ActionStatus,
    AnalyticsOverview
)
from backend.services.llm_service import LLMService
from backend.services.lead_scorer import LeadScorer
from backend.services.proposal_generator import ProposalGenerator
from backend.services.approval_workflow import ApprovalWorkflowService
from backend.services.analytics_service import AnalyticsService
from backend.rag.retriever import RAGRetriever

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cynbit-dealengine")

# FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous Inbound Lead Qualification & Deal Intelligence Copilot for Cynbit Technologies."
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service Instances
llm_service = LLMService()
workflow_service = ApprovalWorkflowService.get_instance()
retriever = RAGRetriever.get_instance()


@app.get("/", tags=["Health"])
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "documentation": "/docs"
    }


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "llm_provider": settings.LLM_PROVIDER,
        "rag_status": "ready",
        "rag_chunks_loaded": len(retriever.doc_store.chunks),
        "pending_human_approvals": len(workflow_service.get_pending_actions())
    }


@app.post("/api/chat", response_model=ChatResponse, tags=["Lead Architect RAG Chat"])
def chat_with_architect(request: ChatRequest):
    """
    Multi-turn consultative dialogue with Cynbit LeadArchitect.
    Grounded in Cynbit knowledge base with source citations and safety guardrails.
    """
    try:
        response_dict = llm_service.generate_chat_response(
            message=request.message,
            history=request.history,
            lead_context=request.lead_context,
            api_key_override=request.api_key_override,
            provider_override=request.provider_override
        )
        return ChatResponse(**response_dict)
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating architectural response: {str(e)}"
        )


@app.post("/api/leads/qualify", response_model=BantScore, tags=["Lead Qualification"])
def qualify_lead(lead: LeadInput):
    """
    Evaluates an inbound lead across BANT dimensions (Budget, Authority, Need, Timeline),
    calculates Deal Fit Score (0-100), intent tier, and recommends technology stack.
    """
    try:
        score = LeadScorer.score_lead(lead)
        return score
    except Exception as e:
        logger.error(f"Lead qualification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error qualifying lead: {str(e)}"
        )


@app.post("/api/proposals/generate", response_model=ProposalBrief, tags=["Proposal Engine"])
def generate_proposal_brief(lead: LeadInput):
    """
    Generates a structured Architectural Discovery Brief and personalized outreach email.
    Automatically enqueues a consequential action for Human-in-the-Loop approval.
    """
    try:
        score = LeadScorer.score_lead(lead)
        brief = ProposalGenerator.generate_proposal(lead, score)

        # Enqueue consequential action in human approval workflow
        action = ApprovalRequest(
            action_id=f"act-{uuid.uuid4().hex[:8]}",
            action_type="DISPATCH_SCOPING_EMAIL",
            lead_name=lead.name,
            company_name=lead.company,
            recipient_email=lead.email,
            email_subject=f"Technical Discovery & Architectural Scoping | Cynbit Technologies ({lead.primary_interest})",
            email_body=brief.drafted_response_email,
            metadata={
                "deal_score": score.total_fit_score,
                "tier": score.tier.value,
                "estimated_value": brief.estimated_total_range,
                "risk_flags": score.risk_flags
            },
            status=ActionStatus.PENDING_APPROVAL
        )
        workflow_service.create_action(action)

        return brief
    except Exception as e:
        logger.error(f"Proposal generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error synthesizing proposal: {str(e)}"
        )


@app.get("/api/actions/pending", response_model=List[ApprovalRequest], tags=["Human Approval"])
def get_pending_approvals():
    """Returns all consequential actions awaiting human architect review."""
    return workflow_service.get_pending_actions()


@app.get("/api/actions/all", response_model=List[ApprovalRequest], tags=["Human Approval"])
def get_all_actions():
    """Returns all actions across pending, approved, and rejected states."""
    return workflow_service.get_all_actions()


@app.post("/api/actions/decision", response_model=ApprovalRequest, tags=["Human Approval"])
def submit_approval_decision(decision: ApprovalDecision):
    """
    Submits a human architect decision (Approve & Dispatch or Reject/Flag).
    Records an immutable audit event.
    """
    try:
        updated_action = workflow_service.process_decision(decision)
        return updated_action
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"Approval error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing approval decision: {str(e)}"
        )


@app.get("/api/kb/sources", tags=["RAG Explorer"])
def get_knowledge_sources():
    """Inspects indexed company documents, chunks, and vector parameters."""
    stats = retriever.get_index_stats()
    sample_chunks = [c.to_dict() for c in retriever.doc_store.chunks[:6]]
    return {
        "index_statistics": stats,
        "preview_chunks": sample_chunks
    }


@app.get("/api/analytics", response_model=AnalyticsOverview, tags=["Executive Analytics"])
def get_analytics():
    """Pipeline velocity, lead distribution, conversion metrics, and ROI metrics."""
    return AnalyticsService.get_overview()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=settings.DEBUG)
