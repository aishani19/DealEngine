from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class IntentTier(str, Enum):
    TIER_1_ENTERPRISE = "Tier 1 - Enterprise High Fit"
    TIER_2_MID_MARKET = "Tier 2 - Mid-Market Qualified"
    TIER_3_EXPLORATORY = "Tier 3 - Exploratory / Early Stage"
    TIER_4_UNQUALIFIED = "Tier 4 - Unqualified / Low Alignment"


class ActionStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISPATCHED = "DISPATCHED"


class Citation(BaseModel):
    source_title: str
    source_file: str
    section: str
    relevance_score: float
    snippet: str


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant' or 'system'")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Prospect inquiry or question")
    history: List[ChatMessage] = Field(default_factory=list)
    lead_context: Optional[Dict[str, Any]] = None
    api_key_override: Optional[str] = None
    provider_override: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    citations: List[Citation] = Field(default_factory=list)
    detected_intent: Optional[str] = None
    fit_assessment: Optional[str] = None
    suggested_actions: List[str] = Field(default_factory=list)
    model_used: str
    latency_ms: float
    tokens_used: int


class LeadInput(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=2)
    company: str = Field(..., min_length=1)
    email: str = Field(..., min_length=5)
    role: Optional[str] = "Decision Maker"
    budget_range: str = Field(..., description="e.g. '$25,000 - $50,000' or '< $5,000'")
    timeline: str = Field(..., description="e.g. 'Immediate', '1 - 3 Months'")
    primary_interest: str = Field(..., description="e.g. 'AI Automation', 'Software Dev', 'TenantEase'")
    inquiry_text: str = Field(..., min_length=10)


class BantScore(BaseModel):
    budget_score: int = Field(..., ge=0, le=25)
    authority_score: int = Field(..., ge=0, le=25)
    need_score: int = Field(..., ge=0, le=25)
    timeline_score: int = Field(..., ge=0, le=25)
    total_fit_score: int = Field(..., ge=0, le=100)
    tier: IntentTier
    budget_analysis: str
    authority_analysis: str
    need_analysis: str
    timeline_analysis: str
    tech_stack_recommendation: List[str]
    risk_flags: List[str]


class PhasedRoadmapStep(BaseModel):
    phase_number: int
    phase_name: str
    duration: str
    key_deliverables: List[str]
    estimated_investment: str


class ProposalBrief(BaseModel):
    lead_id: str
    client_name: str
    company_name: str
    executive_summary: str
    architectural_fit: str
    recommended_domains: List[str]
    phased_roadmap: List[PhasedRoadmapStep]
    estimated_total_range: str
    drafted_response_email: str
    requires_approval: bool = True


class ApprovalRequest(BaseModel):
    action_id: str
    action_type: str = Field(..., description="'DISPATCH_SCOPING_EMAIL' or 'SCHEDULE_DISCOVERY' or 'CRM_SYNC'")
    lead_name: str
    company_name: str
    recipient_email: str
    email_subject: str
    email_body: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: ActionStatus = ActionStatus.PENDING_APPROVAL


class ApprovalDecision(BaseModel):
    action_id: str
    approved: bool
    reviewer_notes: Optional[str] = None
    modified_body: Optional[str] = None
    admin_token: Optional[str] = None


class AnalyticsOverview(BaseModel):
    total_leads_processed: int
    avg_lead_fit_score: float
    leads_by_tier: Dict[str, int]
    avg_latency_seconds: float
    manual_qualification_hours_saved: float
    pipeline_value_identified: str
    rag_documents_indexed: int
    system_status: str
