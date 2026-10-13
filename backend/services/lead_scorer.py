import re
from typing import List, Dict, Any
from backend.models import LeadInput, BantScore, IntentTier


class LeadScorer:
    @staticmethod
    def score_lead(lead: LeadInput) -> BantScore:
        """
        Evaluates an inbound lead using BANT framework and Cynbit service fit heuristics.
        """
        budget_score, budget_analysis = LeadScorer._evaluate_budget(lead.budget_range, lead.inquiry_text)
        authority_score, authority_analysis = LeadScorer._evaluate_authority(lead.role, lead.email)
        need_score, need_analysis, tech_stack = LeadScorer._evaluate_need(lead.primary_interest, lead.inquiry_text)
        timeline_score, timeline_analysis = LeadScorer._evaluate_timeline(lead.timeline, lead.inquiry_text)

        total_score = budget_score + authority_score + need_score + timeline_score

        # Determine Tier
        if total_score >= 80:
            tier = IntentTier.TIER_1_ENTERPRISE
        elif total_score >= 60:
            tier = IntentTier.TIER_2_MID_MARKET
        elif total_score >= 40:
            tier = IntentTier.TIER_3_EXPLORATORY
        else:
            tier = IntentTier.TIER_4_UNQUALIFIED

        # Extract Risk Flags
        risk_flags = LeadScorer._extract_risk_flags(lead, budget_score, timeline_score)

        return BantScore(
            budget_score=budget_score,
            authority_score=authority_score,
            need_score=need_score,
            timeline_score=timeline_score,
            total_fit_score=total_score,
            tier=tier,
            budget_analysis=budget_analysis,
            authority_analysis=authority_analysis,
            need_analysis=need_analysis,
            timeline_analysis=timeline_analysis,
            tech_stack_recommendation=tech_stack,
            risk_flags=risk_flags
        )

    @staticmethod
    def _evaluate_budget(budget_range: str, inquiry: str) -> (int, str):
        b = budget_range.lower()
        if any(w in b for w in ["$40,000", "$50,000", "$60,000", "$70,000", "50k", "70k", "100k"]):
            return 25, "Enterprise Tier budget matches Cynbit full-cycle engineering and dedicated pods ($25k-$70k+)."
        elif any(w in b for w in ["$20,000", "$25,000", "$30,000", "25k"]):
            return 22, "Strong budget aligned with standard Cynbit Autonomous AI Agent build ($15k-$45k)."
        elif any(w in b for w in ["$10,000", "$15,000", "10k", "15k"]):
            return 18, "Adequate for Cynbit Strategic Discovery & MVP Blueprint ($5k-$12k) or TenantEase customization."
        elif any(w in b for w in ["$5,000", "5k"]):
            return 14, "Sufficient for rapid technical discovery sprint or BitElevate educational cohort."
        elif any(w in b for w in ["< $500", "< $1,000", "free", "no budget", "500"]):
            return 2, "Severe budget constraint below Cynbit commercial minimum engagement thresholds."
        return 12, "Budget exploratory or unverified; requires Discovery Audit to scope capital allocation."

    @staticmethod
    def _evaluate_authority(role: str, email: str) -> (int, str):
        r = (role or "").lower()
        e = (email or "").lower()
        is_corporate_email = not any(free in e for free in ["@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com"])

        score = 0
        analysis = []
        if any(exec_title in r for exec_title in ["vp", "director", "cpo", "cto", "ceo", "founder", "head of", "managing director"]):
            score += 20
            analysis.append(f"High-authority economic buyer / executive title ('{role}').")
        elif any(mid in r for mid in ["manager", "lead", "engineer", "architect", "dean"]):
            score += 15
            analysis.append(f"Technical influencer / departmental sponsor ('{role}').")
        elif any(low in r for low in ["student", "intern", "hobbyist"]):
            score += 4
            analysis.append("Individual student / non-commercial sponsor.")
        else:
            score += 10
            analysis.append("Unspecified authority level.")

        if is_corporate_email:
            score += 5
            analysis.append("Verified enterprise domain email.")
        else:
            analysis.append("Public/free email domain provided.")

        return min(25, score), " ".join(analysis)

    @staticmethod
    def _evaluate_need(interest: str, inquiry: str) -> (int, str, List[str]):
        i = inquiry.lower()
        int_str = interest.lower()
        
        tech_stack = ["FastAPI", "Python", "Next.js", "Docker"]
        need_score = 15
        analysis_parts = []

        if any(w in i or w in int_str for w in ["agent", "ai automation", "llm", "rag", "multi-agent"]):
            need_score += 10
            tech_stack = ["LangChain / LangGraph", "FastAPI", "PostgreSQL + pgvector", "Llama 3 / Mistral", "Redis"]
            analysis_parts.append("High alignment with Cynbit's core Autonomous AI Agents & Enterprise RAG practice.")
        elif any(w in i or w in int_str for w in ["tenant", "property", "tenantease", "real estate"]):
            need_score += 9
            tech_stack = ["TenantEase Core Engine", "Next.js 14", "FastAPI", "WhatsApp Business API", "Razorpay / Stripe"]
            analysis_parts.append("Direct alignment with Cynbit's TenantEase SaaS product ecosystem.")
        elif any(w in i or w in int_str for w in ["bitelevate", "student", "train", "upskill", "academy"]):
            need_score += 8
            tech_stack = ["BitElevate LMS", "Architectural Coding Labs", "GitHub Classroom"]
            analysis_parts.append("Aligned with BitElevate unstructured learning and corporate mentorship program.")
        elif any(w in i or w in int_str for w in ["cloud", "aws", "azure", "devops", "zero-trust"]):
            need_score += 9
            tech_stack = ["AWS EKS / ECS", "Terraform IaC", "Docker", "Cloudflare Zero-Trust", "Datadog / Prometheus"]
            analysis_parts.append("Strong fit for Cynbit's Cloud Infrastructure & Zero-Trust migration practice.")
        elif any(w in i for w in ["homework", "free code", "assignment"]):
            need_score = 4
            tech_stack = ["Open Source Resources"]
            analysis_parts.append("Academic homework request with no commercial engineering scope.")
        else:
            analysis_parts.append("Broad custom software inquiry; fits general full-stack engineering.")

        return min(25, need_score), " ".join(analysis_parts), tech_stack

    @staticmethod
    def _evaluate_timeline(timeline: str, inquiry: str) -> (int, str):
        t = (timeline or "").lower()
        if any(w in t for w in ["immediate", "30 days", "within a month", "urgent"]):
            return 25, "Urgent delivery timeline (<30 days); high purchase intent and immediate discovery needed."
        elif any(w in t for w in ["1 - 3 months", "1 - 2 months", "60 days", "quarter"]):
            return 22, "Standard enterprise procurement window (1-3 months); ideal for Discovery -> Blueprint lifecycle."
        elif any(w in t for w in ["3 - 6 months", "future"]):
            return 16, "Mid-term planning horizon; suitable for nurture sequence and architectural roadmap consultation."
        elif any(w in t for w in ["uncertain", "just exploring", "tomorrow", "tonight"]):
            return 6, "Impulsive or undefined timeline indicating low qualification confidence."
        return 14, "Flexible timeline requiring discovery alignment."

    @staticmethod
    def _extract_risk_flags(lead: LeadInput, budget_score: int, timeline_score: int) -> List[str]:
        flags = []
        i = lead.inquiry_text.lower()
        
        if budget_score < 10:
            flags.append("Budget Deficit: Inquired funds below Cynbit commercial threshold.")
        if any(w in i for w in ["tomorrow", "tonight", "urgent without scope"]):
            flags.append("Timeline Risk: Unrealistic turnaround without architectural specification.")
        if any(w in i for w in ["homework", "assignment", "free"]):
            flags.append("Commercial Fit Risk: Non-commercial educational inquiry.")
        if len(lead.inquiry_text.split()) < 15:
            flags.append("Vague Requirements: Insufficient technical depth provided in initial inquiry.")
        if not flags:
            flags.append("Low Risk: High-quality enterprise parameters with clear architectural alignment.")
        return flags
