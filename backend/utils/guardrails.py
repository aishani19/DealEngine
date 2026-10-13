import re
from typing import Tuple, Optional


# Prompt Injection and Jailbreak patterns
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(the\s+)?system\s+prompt",
    r"you\s+are\s+now\s+in\s+dan\s+mode",
    r"pretend\s+you\s+are\s+an\s+unfiltered\s+ai",
    r"bypass\s+all\s+safety\s+filters",
    r"reveal\s+your\s+(internal\s+)?system\s+prompt",
    r"show\s+me\s+your\s+hidden\s+rules",
    r"act\s+as\s+a\s+malicious",
]

# Sensitive patterns for masking
PHONE_PATTERN = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")


def check_prompt_injection(user_input: str) -> Tuple[bool, Optional[str]]:
    """
    Detects attempts to manipulate, jailbreak or leak system instructions.
    Returns (is_injection, reason)
    """
    cleaned = user_input.lower().strip()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return True, "Potential prompt injection or policy bypass pattern detected."
    return False, None


def sanitize_input(user_input: str) -> str:
    """
    Masks overly sensitive financial identifiers while retaining business contact info.
    """
    # Mask credit card numbers if any
    sanitized = CREDIT_CARD_PATTERN.sub("[MASKED_CARD_NUMBER]", user_input)
    return sanitized.strip()


def is_cynbit_relevant(query: str) -> bool:
    """
    Determines whether the query is aligned with Cynbit's core domains:
    AI, agents, software engineering, cloud architecture, SaaS (TenantEase, Revio, Cynbit Studio),
    BitElevate, case studies, or business consulting.
    """
    query_lower = query.lower()
    
    # Generic conversational greetings are always allowed
    greetings = ["hi", "hello", "hey", "greetings", "good morning", "good evening", "who are you", "what can you do"]
    if any(query_lower.strip().startswith(g) for g in greetings):
        return True
        
    relevant_keywords = [
        "ai", "agent", "llm", "rag", "software", "app", "web", "mobile", "cloud", "aws", "azure",
        "tenantease", "revio", "cynbit", "studio", "bitelevate", "architect", "pricing", "cost",
        "quote", "services", "consult", "hiring", "developer", "engineering", "seo", "mvp",
        "jaipur", "development", "database", "backend", "frontend", "infrastructure", "devops",
        "automation", "case study", "portfolio", "timeline", "budget", "discovery"
    ]
    
    return any(kw in query_lower for kw in relevant_keywords)
