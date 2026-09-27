import os
from pathlib import Path
from typing import Any, Dict
import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CONFIG_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "PCOS Longitudinal Tracker Backend"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR}/pcos_tracker.db")
    
    # LLM Settings (Groq API)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    # Default to llama-3.3-70b-versatile or current Groq flagship
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Path to scoring config yaml
    SCORING_CONFIG_PATH: Path = CONFIG_DIR / "scoring_config.yaml"
    
    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env",
        extra="ignore"
    )

settings = Settings()

def load_scoring_config() -> Dict[str, Any]:
    with open(settings.SCORING_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
