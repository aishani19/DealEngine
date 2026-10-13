import time
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import requests

from backend.config import settings
from backend.models import ChatMessage, Citation
from backend.rag.retriever import RAGRetriever
from backend.utils.guardrails import check_prompt_injection, is_cynbit_relevant, sanitize_input

logger = logging.getLogger(__name__)

CYNBIT_SYSTEM_PROMPT = """You are Cynbit LeadArchitect, the senior AI solutions architect and sales intelligence copilot for Cynbit Technologies (Jaipur, India).
Your brand archetype is 'The Optimistic Architect'—rigorous, technical, agile, and laser-focused on enterprise business outcomes.

Key Guidelines:
1. Ground your answers strictly in Cynbit's factual knowledge base:
   - 4 Service Domains: AI Automation (autonomous agents, custom LLMs, RAG), Software Engineering (Next.js, FastAPI, mobile), Cloud Infrastructure (AWS/Azure zero-trust), and Technical SEO.
   - Proprietary Products: Cynbit Studio (career intelligence), Revio (AI review assistant), TenantEase (property management).
   - Education: BitElevate (1000+ architects trained, hands-on tracks).
   - Case Studies: Marketing Addict (+40% organic leads), Evento (50k+ concurrent users, 0 latency), Urban Wardrobe (99.9% uptime).
   - Process: 6-Step Architectural Lifecycle (Discovery, Blueprint, Design, Implementation, QA, Deploy).
2. Maintain a consultative, senior architect tone. Be concise, precise, and structured.
3. Proactively qualify inbound prospect requirements: ask clarifying questions regarding budget, timeline, existing tech stack, and user scale.
4. When citing information, mention the relevant Cynbit capability or case study accurately.
5. Never hallucinate pricing guarantees; quote typical sprint tiers ($5k-$45k) and recommend a formal Discovery Audit.
"""


class LLMService:
    def __init__(self):
        self.retriever = RAGRetriever.get_instance()

    def generate_chat_response(
        self,
        message: str,
        history: List[ChatMessage] = None,
        lead_context: Optional[Dict[str, Any]] = None,
        api_key_override: Optional[str] = None,
        provider_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes a prospect query through RAG retrieval, guardrails, and real LLM (or deterministic demo engine).
        """
        start_time = time.time()
        history = history or []
        
        # 1. Guardrail: Prompt injection check
        is_injection, reason = check_prompt_injection(message)
        if is_injection:
            return {
                "reply": f"Security Alert: Your inquiry triggered our prompt integrity guardrail ({reason}). At Cynbit Technologies, we adhere strictly to enterprise zero-trust security standards. How can I assist with your software, AI automation, or cloud engineering requirements?",
                "citations": [],
                "detected_intent": "Security / Guardrail Trigger",
                "fit_assessment": "Unqualified",
                "suggested_actions": ["Reset chat context", "Ask about AI Automation services"],
                "model_used": "cynbit-guardrail-v1",
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "tokens_used": 45
            }

        # 2. Sanitize input
        cleaned_query = sanitize_input(message)

        # 3. Off-topic check
        if not is_cynbit_relevant(cleaned_query):
            citations = self.retriever.retrieve_citations("Cynbit Services and AI Automation Overview", top_k=2)
            return {
                "reply": "I am Cynbit's LeadArchitect copilot, specialized exclusively in engineering consultations for Cynbit Technologies. I can help you evaluate Autonomous AI Agents, custom software development, cloud infrastructure on AWS/Azure, SaaS solutions like TenantEase & Revio, or BitElevate engineering programs. Could you share what system or product you're looking to build?",
                "citations": citations,
                "detected_intent": "Off-Topic Redirect",
                "fit_assessment": "Exploratory",
                "suggested_actions": [
                    "Explore AI Automation & Agents",
                    "Ask about TenantEase SaaS",
                    "Inquire about BitElevate Training"
                ],
                "model_used": "cynbit-intent-router",
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "tokens_used": 65
            }

        # 4. RAG Retrieval
        citations = self.retriever.retrieve_citations(cleaned_query, top_k=3)
        context_block = "\n\n".join([f"Source: {c.source_title} ({c.section})\n{c.snippet}" for c in citations])

        # 5. Determine active credentials
        groq_key = api_key_override if (provider_override == "groq" and api_key_override) else settings.GROQ_API_KEY
        openai_key = api_key_override if (provider_override == "openai" and api_key_override) else settings.OPENAI_API_KEY
        provider = provider_override or settings.LLM_PROVIDER

        # 6. Call Real LLM or Fallback to Demo Engine
        if provider == "groq" and groq_key:
            reply_text, model_name, tokens = self._call_groq(cleaned_query, history, context_block, groq_key)
        elif provider == "openai" and openai_key:
            reply_text, model_name, tokens = self._call_openai(cleaned_query, history, context_block, openai_key)
        else:
            # Deterministic High-Fidelity Demo Simulation
            reply_text, model_name, tokens = self._generate_high_fidelity_demo(cleaned_query, context_block, citations)

        # Detect intent and suggested next actions
        intent, fit, actions = self._classify_intent_and_actions(cleaned_query, reply_text)

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "reply": reply_text,
            "citations": citations,
            "detected_intent": intent,
            "fit_assessment": fit,
            "suggested_actions": actions,
            "model_used": model_name,
            "latency_ms": latency_ms,
            "tokens_used": tokens
        }

    def _call_groq(self, query: str, history: List[ChatMessage], context: str, api_key: str) -> Tuple[str, str, int]:
        try:
            messages = [{"role": "system", "content": f"{CYNBIT_SYSTEM_PROMPT}\n\nRELEVANT CYNBIT CONTEXT:\n{context}"}]
            for h in history[-4:]:
                messages.append({"role": h.role, "content": h.content})
            messages.append({"role": "user", "content": query})

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 600
                },
                timeout=12
            )
            if response.status_code == 200:
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 350)
                return text, "Groq / llama-3.3-70b-versatile (Live)", tokens
            else:
                logger.warning(f"Groq API returned {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Groq call failed: {e}")

        # Fallback if API call errored
        return self._generate_high_fidelity_demo(query, context, [])

    def _call_openai(self, query: str, history: List[ChatMessage], context: str, api_key: str) -> Tuple[str, str, int]:
        try:
            messages = [{"role": "system", "content": f"{CYNBIT_SYSTEM_PROMPT}\n\nRELEVANT CYNBIT CONTEXT:\n{context}"}]
            for h in history[-4:]:
                messages.append({"role": h.role, "content": h.content})
            messages.append({"role": "user", "content": query})

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 600
                },
                timeout=12
            )
            if response.status_code == 200:
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 350)
                return text, "OpenAI / gpt-4o-mini (Live)", tokens
            else:
                logger.warning(f"OpenAI API returned {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")

        # Fallback if API call errored
        return self._generate_high_fidelity_demo(query, context, [])

    def _generate_high_fidelity_demo(self, query: str, context: str, citations: List[Citation]) -> Tuple[str, str, int]:
        """
        Deterministic, highly professional simulation engine that synthesizes retrieved context
        into rich, structured responses when no API key is provided.
        """
        q = query.lower()
        
        if any(w in q for w in ["ai", "agent", "llm", "automation", "rag", "bot"]):
            reply = (
                "At Cynbit Technologies, our **AI Automation & Autonomous Agents** practice builds cognitive workflows "
                "that run independently to solve complex operational bottlenecks.\n\n"
                "**Key Technical Capabilities:**\n"
                "• **Multi-Agent Orchestration:** Autonomous task-solving agents using LangChain and LangGraph for customer triage, sales qualification, and logistics.\n"
                "• **Enterprise RAG Systems:** Zero-hallucination semantic search over your private documentation, databases, and APIs with source citations.\n"
                "• **Model Fine-Tuning & Quantization:** Tailored open-weight models (Llama 3, Mistral) or API-based engines optimized for high throughput and sub-500ms latency.\n\n"
                "**Proven Track Record:** For our client *Evento*, our optimistic architecture and AI automation handled 50,000+ concurrent users with zero latency.\n\n"
                "To scope an AI engagement, we typically start with a **2-week Discovery & Blueprint Audit ($5,000 - $12,000)** before technical implementation. What specific workflow or user volume are you aiming to automate?"
            )
        elif any(w in q for w in ["tenant", "property", "tenantease", "rent", "landlord"]):
            reply = (
                "**TenantEase** is Cynbit's proprietary property management ecosystem designed for landlords, co-living operators, "
                "and real estate asset managers.\n\n"
                "**What TenantEase Delivers:**\n"
                "• **Automated Rent Collection:** Integrated bank transfers and WhatsApp payment reminders that drastically reduce late payments.\n"
                "• **Smart Maintenance Dispatch:** Photo-based issue logging, contractor routing, and real-time repair status tracking.\n"
                "• **Digital KYC & Lease Agreements:** Paperless onboarding with verified identity records and digital signatures.\n"
                "• **Portfolio Analytics:** Occupancy rates, yield forecasting, and expense tracking across multi-city properties.\n\n"
                "We offer TenantEase both as a ready-to-deploy SaaS and with custom enterprise integrations. Would you like to schedule a product demo or discuss white-labeling for your portfolio?"
            )
        elif any(w in q for w in ["coaching", "institute", "school", "college", "batch", "academy", "portal", "lms", "student management", "fee management"]):
            reply = (
                "For educational organizations and coaching institutes, Cynbit Technologies architects "
                "**Custom Institutional Management Portals & Web Systems** under our Software Engineering domain.\n\n"
                "**Recommended Technical Architecture:**\n"
                "• **Batch & Course Scheduling:** Real-time batch allocation, attendance monitoring, and timetable coordination.\n"
                "• **Fee Management & Invoicing:** Integrated online payment gateways (Razorpay/Stripe) with automated fee receipt generation and WhatsApp payment reminders.\n"
                "• **Student & Parent Portal:** Modern Next.js responsive web application with student performance reports and notice boards.\n"
                "• **Secure Cloud Backend:** FastAPI/PostgreSQL backend hosted on AWS with role-based access control (Admin, Teacher, Student).\n\n"
                "We typically engineer institutional platforms in **4 to 6 weeks** starting with our Discovery & Blueprint phase. What is your estimated student volume?"
            )
        elif any(w in q for w in ["website", "web app", "software development", "mobile app", "full stack"]):
            reply = (
                "Cynbit Technologies' **Software Engineering** practice builds enterprise-grade, high-performance "
                "web and mobile applications using modern frameworks like Next.js, React Native, FastAPI, and PostgreSQL.\n\n"
                "**Our Architectural Standards:**\n"
                "• **Optimistic UI & Sub-Second Latency:** Seamless, responsive user experience modeled after our high-scale work with Evento (50k+ concurrent users).\n"
                "• **API-First Microservices:** Modular, clean codebases designed for easy third-party API integrations (payments, SMS, CRM).\n"
                "• **Zero-Trust Cloud Hosting:** Containerized deployment on AWS or Azure with automated CI/CD pipelines.\n\n"
                "Would you like to scope your web platform through our Discovery & Blueprint phase ($5,000 - $12,000)?"
            )
        elif any(w in q for w in ["pricing", "cost", "budget", "quote", "rate"]):
            reply = (
                "Cynbit structures engagements through our **6-Step Architectural Lifecycle** to maximize transparency and ROI:\n\n"
                "1. **Strategic Discovery & Blueprint ($5,000 - $12,000 | 2–4 Weeks):** Full audit of your workflows, system architecture design, and technical feasibility blueprint.\n"
                "2. **Full Architectural Build & Custom AI Agent Engine ($15,000 - $45,000 | 6–12 Weeks):** Sprint-based engineering, production RAG/LLM pipelines, and resilient web/mobile interfaces.\n"
                "3. **Enterprise DevSecOps Retainer ($8,000 - $20,000/mo):** Dedicated engineering pod, 24/7 cloud reliability, and continuous iteration.\n\n"
                "What is your target timeline and scope? I can generate a tailored architectural proposal brief for your team."
            )
        elif any(w in q for w in ["bitelevate", "train", "course", "learn", "student", "career"]):
            reply = (
                "**BitElevate** is Cynbit's unstructured learning and engineering mentorship ecosystem. "
                "With over 1,000+ certified software architects trained, BitElevate bridges the gap between academic theory and enterprise mastery.\n\n"
                "**Core Learning Paths:**\n"
                "• **AI Engineering & Autonomous Agents:** LLM orchestration, RAG pipelines, and vector databases.\n"
                "• **Full-Stack Software Architecture:** Modern Next.js, FastAPI, microservices, and optimistic UI design.\n"
                "• **Cloud & DevSecOps:** AWS/Azure zero-trust deployment, Docker, and Kubernetes.\n\n"
                "We partner with both ambitious individual developers and universities/enterprises seeking cohort upskilling. How can we help your team or cohort?"
            )
        elif any(w in q for w in ["case study", "client", "portfolio", "review", "work", "example"]):
            reply = (
                "Here are several representative success stories architected by Cynbit Technologies:\n\n"
                "• **Marketing Addict (Technical SEO & Platform):** Refactored legacy architecture to modern Next.js; achieved a **+40% increase in organic leads**.\n"
                "• **Evento (Enterprise SaaS & AI):** Engineered an optimistic cloud architecture that sustained **50,000+ concurrent users with zero latency**.\n"
                "• **Urban Wardrobe (Global Retail):** Multi-region AWS zero-trust deployment delivering **99.9% uptime across international markets**.\n"
                "• **Cloudy Tales (Digital Experience):** 100% on-time full-cycle delivery uniting interactive storytelling with subscription memberships.\n\n"
                "Which domain aligns closest with your goals—AI Automation, Full-Stack Engineering, or Cloud Infrastructure?"
            )
        else:
            reply = (
                "Welcome to **Cynbit Technologies**—we architect the digital future with autonomous AI agents, "
                "custom software development, and scalable cloud platforms.\n\n"
                "Based in Jaipur, Rajasthan, we serve global clients across four core domains:\n"
                "1. **AI Automation:** Autonomous multi-agent systems and enterprise RAG engines.\n"
                "2. **Software Engineering:** High-performance web and mobile applications (Next.js, FastAPI, React Native).\n"
                "3. **Cloud Infrastructure:** Zero-trust architecture on AWS and Azure with 99.9% uptime SLAs.\n"
                "4. **Technical SEO:** Data-driven organic growth and ROI engines.\n\n"
                "Could you describe your project goals, user volume, or target timeline so I can guide you to the right architecture?"
            )

        model_name = "Cynbit Neural Engine (Deterministic High-Fidelity Demo)"
        tokens = int(len(reply.split()) * 1.35)
        return reply, model_name, tokens

    def _classify_intent_and_actions(self, query: str, reply: str) -> Tuple[str, str, List[str]]:
        q = query.lower()
        if any(w in q for w in ["ai", "agent", "llm", "automation"]):
            return (
                "AI Automation Discovery",
                "Tier 1 - High Priority Enterprise Fit",
                ["Generate AI Architecture Brief", "Schedule Technical Discovery Call", "Run BANT Qualification"]
            )
        elif any(w in q for w in ["tenant", "property", "tenantease"]):
            return (
                "TenantEase SaaS Inquiry",
                "Tier 1 - Product Fit",
                ["Book TenantEase Demo", "Calculate Portfolio Pricing", "Request Custom Integrations"]
            )
        elif any(w in q for w in ["price", "cost", "budget", "quote"]):
            return (
                "Commercial Scoping & Pricing",
                "Tier 2 - Qualified Commercial",
                ["View 6-Step Lifecycle Breakdown", "Download Scope Template", "Request Discovery Audit"]
            )
        elif any(w in q for w in ["bitelevate", "learn", "student", "career"]):
            return (
                "BitElevate Training Track",
                "Tier 2 - Educational Track",
                ["Explore Learning Paths", "Review Student Diaries", "Enroll Cohort"]
            )
        return (
            "General Architectural Discovery",
            "Tier 2 - Exploratory",
            ["Explore Services Hub", "Read Client Case Studies", "Speak with Lead Architect"]
        )
