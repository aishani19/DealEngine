import time
import uuid
from typing import Dict, List, Optional
from datetime import datetime

from backend.models import ApprovalRequest, ApprovalDecision, ActionStatus


class ApprovalWorkflowService:
    _instance = None

    def __init__(self):
        # In-memory store for action items
        self.actions: Dict[str, ApprovalRequest] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self._seed_sample_actions()

    @classmethod
    def get_instance(cls) -> "ApprovalWorkflowService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _seed_sample_actions(self):
        """Pre-populates pending consequential actions for realistic review."""
        sample_action = ApprovalRequest(
            action_id="act-apex-001",
            action_type="DISPATCH_SCOPING_EMAIL",
            lead_name="Sarah Jenkins",
            company_name="Apex Logistics Group",
            recipient_email="s.jenkins@apexlogistics.com",
            email_subject="Technical Discovery & AI Autonomous Agent Architecture | Cynbit Technologies",
            email_body=(
                "Dear Sarah,\n\n"
                "Thank you for contacting Cynbit Technologies. We reviewed Apex Logistics Group's inquiry regarding an "
                "autonomous AI multi-agent workflow for your 450-freight dispatch operation.\n\n"
                "Given your volume of 2,000+ daily tickets, we recommend our 6-step lifecycle beginning with a 2-Week "
                "Discovery & Architectural Audit ($6,500) focusing on telematics ingestion and LangGraph agent routing.\n\n"
                "Would Thursday at 4:30 PM IST work for a discovery call with our Principal Architect?\n\n"
                "Best regards,\nCynbit Solutions Team"
            ),
            metadata={
                "deal_score": 94,
                "tier": "Tier 1 - Enterprise High Fit",
                "estimated_value": "$38,000",
                "risk_level": "Low"
            },
            status=ActionStatus.PENDING_APPROVAL
        )
        self.actions[sample_action.action_id] = sample_action

        sample_action_2 = ApprovalRequest(
            action_id="act-horizon-002",
            action_type="SCHEDULE_DISCOVERY",
            lead_name="Rajiv Mehra",
            company_name="Horizon Realty Partners",
            recipient_email="rajiv.mehra@horizonrealty.in",
            email_subject="TenantEase Portfolio Customization Demo & Discovery Session",
            email_body=(
                "Dear Rajiv,\n\n"
                "We would be delighted to demonstrate how TenantEase handles automated rent collection, "
                "WhatsApp payment reminders, and digital maintenance dispatch across your 1,200 residential units.\n\n"
                "Please choose a convenient slot on our executive calendar: https://cal.cynbit.in/discovery-arch\n\n"
                "Best regards,\nCynbit SaaS Operations"
            ),
            metadata={
                "deal_score": 87,
                "tier": "Tier 1 - SaaS Portfolio Fit",
                "estimated_value": "$18,500",
                "risk_level": "Low"
            },
            status=ActionStatus.PENDING_APPROVAL
        )
        self.actions[sample_action_2.action_id] = sample_action_2

    def create_action(self, request: ApprovalRequest) -> ApprovalRequest:
        self.actions[request.action_id] = request
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action_id": request.action_id,
            "event": "CREATED",
            "details": f"Consequential action created for {request.company_name} ({request.action_type})"
        })
        return request

    def get_pending_actions(self) -> List[ApprovalRequest]:
        return [act for act in self.actions.values() if act.status == ActionStatus.PENDING_APPROVAL]

    def get_all_actions(self) -> List[ApprovalRequest]:
        return list(self.actions.values())

    def get_action_by_id(self, action_id: str) -> Optional[ApprovalRequest]:
        return self.actions.get(action_id)

    def process_decision(self, decision: ApprovalDecision) -> ApprovalRequest:
        action = self.actions.get(decision.action_id)
        if not action:
            raise ValueError(f"Action ID {decision.action_id} not found.")

        timestamp = datetime.now().isoformat()
        if decision.approved:
            action.status = ActionStatus.APPROVED
            if decision.modified_body:
                action.email_body = decision.modified_body

            # Log audit
            self.audit_log.append({
                "timestamp": timestamp,
                "action_id": action.action_id,
                "event": "APPROVED_AND_DISPATCHED",
                "reviewer_notes": decision.reviewer_notes or "Approved by Principal Architect",
                "recipient": action.recipient_email
            })
            action.status = ActionStatus.DISPATCHED
        else:
            action.status = ActionStatus.REJECTED
            self.audit_log.append({
                "timestamp": timestamp,
                "action_id": action.action_id,
                "event": "REJECTED",
                "reviewer_notes": decision.reviewer_notes or "Rejected / Flagged during review",
                "recipient": action.recipient_email
            })

        return action
