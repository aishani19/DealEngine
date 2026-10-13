import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KB_DIR = DATA_DIR / "knowledge_base"


class Settings(BaseSettings):
    APP_NAME: str = "Cynbit DealEngine"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Network
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "8501"))
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")  # 'groq' or 'openai' or 'demo'
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile")
    
    # RAG Settings
    TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", "4"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.20"))
    
    # Governance & Approval
    REQUIRE_HUMAN_APPROVAL_FOR_DISPATCH: bool = os.getenv("REQUIRE_HUMAN_APPROVAL_FOR_DISPATCH", "true").lower() == "true"
    ADMIN_APPROVAL_TOKEN: str = os.getenv("ADMIN_APPROVAL_TOKEN", "cynbit_secure_architect_key_2026")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
