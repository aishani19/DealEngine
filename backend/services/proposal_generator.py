import uuid
from typing import Dict, Any, List
from backend.models import LeadInput, BantScore, ProposalBrief, PhasedRoadmapStep, ApprovalRequest, ActionStatus


class ProposalGenerator:
    @staticmethod
    def generate_proposal(lead: LeadInput, score: BantScore) -> ProposalBrief:
        """
        Synthesizes a structured Architectural Discovery Brief and personalized client scoping email.
        """
        lead_id = lead.id or f"lead-{uuid.uuid4().hex[:6]}"
        
        # 1. Executive Summary
        exec_summary = (
            f"Discovery scoping evaluation for {lead.company} regarding {lead.primary_interest}. "
            f"Prospect scored a total Deal Fit of {score.total_fit_score}/100 ({score.tier.value}). "
            f"Inquiry indicates a strong opportunity for Cynbit to engineer scalable, optimistic architecture."
        )

        # 2. Architectural Fit
        arch_fit = (
            f"{score.need_analysis} Proposed technology stack includes: {', '.join(score.tech_stack_recommendation)}. "
            f"Leverages Cynbit's battle-tested patterns (e.g., Evento high-concurrency model and zero-trust cloud foundations)."
        )

        # 3. Phased Roadmap based on Cynbit Lifecycle
        if score.total_fit_score >= 60:
            roadmap = [
                PhasedRoadmapStep(
                    phase_number=1,
                    phase_name="Discovery & Architectural Audit",
                    duration="1 - 2 Weeks",
                    key_deliverables=[
                        "Deep-dive audit into workflows and existing APIs",
                        "Technical Debt & Bottleneck Assessment",
                        "Formal Architectural Blueprint & Data Pipeline Schema"
                    ],
                    estimated_investment="$5,000 - $8,000"
                ),
                PhasedRoadmapStep(
                    phase_number=2,
                    phase_name="Core Engine Development & Prototyping",
                    duration="3 - 5 Weeks",
                    key_deliverables=[
                        "Implementation of core microservices / AI multi-agent workflows",
                        "Vector embedding & retrieval pipeline integration",
                        "Interactive proof-of-concept validation with test data"
                    ],
                    estimated_investment="$12,000 - $20,000"
                ),
                PhasedRoadmapStep(
                    phase_number=3,
                    phase_name="Zero-Trust Cloud Deployment & Observability",
                    duration="2 - 3 Weeks",
                    key_deliverables=[
                        "Containerized deployment on AWS / Azure with automated CI/CD",
                        "Load testing, security hardening, and SLA monitoring",
                        "Production handoff & team onboarding"
                    ],
                    estimated_investment="$8,000 - $14,000"
                )
            ]
            total_est = "$25,000 - $42,000 (Across 3 Sprints)"
        else:
            roadmap = [
                PhasedRoadmapStep(
                    phase_number=1,
                    phase_name="Strategic Advisory & Scope Calibration",
                    duration="1 Week",
                    key_deliverables=[
                        "Requirement clarification session",
                        "Technical feasibility evaluation",
                        "Recommendation for off-the-shelf vs custom build"
                    ],
                    estimated_investment="$1,500 - $3,000"
                )
            ]
            total_est = "$1,500 - $3,000 (Advisory Track)"

        # 4. Drafted Outreach Email
        drafted_email = ProposalGenerator._draft_scoping_email(lead, score, roadmap, total_est)

        return ProposalBrief(
            lead_id=lead_id,
            client_name=lead.name,
            company_name=lead.company,
            executive_summary=exec_summary,
            architectural_fit=arch_fit,
            recommended_domains=[lead.primary_interest, "Cloud Infrastructure"],
            phased_roadmap=roadmap,
            estimated_total_range=total_est,
            drafted_response_email=drafted_email,
            requires_approval=True
        )

    @staticmethod
    def _draft_scoping_email(lead: LeadInput, score: BantScore, roadmap: List[PhasedRoadmapStep], total_est: str) -> str:
        """Personalized email tailored to lead's requirements and tone."""
        email = f"""Dear {lead.name},

Thank you for reaching out to Cynbit Technologies regarding your interest in {lead.primary_interest} for {lead.company}.

Our architectural team in Jaipur reviewed your requirements:
"{lead.inquiry_text.strip()}"

At Cynbit, we operate as 'The Optimistic Architect'—combining startup agility with enterprise rigor. To address your goals, we recommend a phased deployment framework:

1. Phase 1: {roadmap[0].phase_name} ({roadmap[0].duration})
   Deliverables: {', '.join(roadmap[0].key_deliverables)}
2. Target Architecture Stack: {', '.join(score.tech_stack_recommendation)}

Similar to our work with high-scale partners like Evento (handling 50,000+ concurrent users with zero latency), we ensure each milestone is benchmarked for measurable ROI and zero-trust reliability.

We would love to invite you to a 30-minute Technical Discovery Session with our Principal Solutions Architect this week. 

Are you available for a brief call on Thursday at 3:00 PM IST (or your local equivalent)?

Warm regards,

Principal Solutions Architect
Cynbit Technologies | Jaipur, India
opportunities@cynbit.in | https://www.cynbit.in
"""
        return email.strip()
