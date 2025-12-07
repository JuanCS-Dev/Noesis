"""
Configuração do Maximus Core Service
====================================

Configurações centralizadas via Pydantic Settings.
"""

from pydantic import BaseModel, Field
from functools import lru_cache
import os

class LLMSettings(BaseModel):
    """Configurações do LLM (Gemini)."""
    api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", "fake_key"))
    model: str = "gemini-3.0-pro-001"
    temperature: float = 0.7
    max_tokens: int = 8192
    timeout: int = 60
    thinking_level: str = "HIGH"
    enable_thought_signatures: bool = True

class Settings(BaseModel):
    """Configurações globais."""
    llm: LLMSettings = Field(default_factory=LLMSettings)

@lru_cache()
def get_settings() -> Settings:
    """Retorna instância única das configurações."""
    return Settings()
