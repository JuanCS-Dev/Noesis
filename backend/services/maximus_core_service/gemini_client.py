"""
Gemini Client - Google Gemini Integration for Maximus AI
========================================================

Cliente para Google Gemini (versão 3.0) com suporte a:
- Text generation com Thinking Config (Chain-of-Thought nativo)
- Tool calling (function calling)
- Embeddings
- Thought Signatures (metacognição)
- Temporal Grounding (Contexto de Data/Hora)

Model: gemini-3.0-pro-001
"""

from __future__ import annotations

import os
import logging
import json
from dataclasses import dataclass
from typing import Any
from datetime import datetime

import httpx

from .config import get_settings

logger = logging.getLogger(__name__)

@dataclass
class GeminiConfig:
    """Configuração do Gemini (Legacy wrapper for backward compat)"""
    api_key: str
    model: str = "gemini-3.0-pro-001"
    temperature: float = 0.7
    max_tokens: int = 8192
    timeout: int = 60
    thinking_level: str = "HIGH"
    enable_thought_signatures: bool = True


class GeminiClient:
    """
    Cliente para Google Gemini API v1beta (Gemini 3.0 Ready).
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, config: GeminiConfig | None = None):
        # Use provided config or load from global settings
        if config is None:
            settings = get_settings().llm
            self.config = GeminiConfig(
                api_key=settings.api_key,
                model=settings.model,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                timeout=settings.timeout,
                thinking_level=settings.thinking_level,
                enable_thought_signatures=settings.enable_thought_signatures
            )
        else:
            self.config = config

        self.api_key = self.config.api_key
        self.model = self.config.model
        
        # Sanity Check Log (Cyberpunk Style)
        self._log_boot_status()

    def _log_boot_status(self):
        """Exibe status de inicialização do link neural."""
        print(
            f"🟢 DAIMON LINK ESTABLISHED | "
            f"Model: {self.model} | "
            f"Thinking: {self.config.thinking_level} | "
            f"Signatures: {'ACTIVE' if self.config.enable_thought_signatures else 'INACTIVE'}"
        )

    def _get_temporal_context(self) -> str:
        """Gera o contexto temporal atual para aterramento."""
        current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M")
        return (
            f"SYSTEM OVERRIDE: Current Operational Date is {current_time} (2025 Context). "
            f"You are running on Gemini 3.0 Pro High hardware."
        )

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        tools: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        previous_thought_signature: str | None = None,
    ) -> dict[str, Any]:
        """
        Gera texto usando Gemini 3.0 com Thinking Config.
        """
        url = f"{self.BASE_URL}/models/{self.model}:generateContent"

        # Configuração de Thinking (Novo em v1beta/3.0)
        thinking_config = {}
        if self.config.thinking_level:
            thinking_config = {
                "includeThoughts": True,
                "thinkingLevel": self.config.thinking_level
            }

        # Build request
        generation_config = {
            "temperature": temperature or self.config.temperature,
            "maxOutputTokens": max_tokens or self.config.max_tokens,
        }
        
        # Add thinking config if enabled (Gemini specific structure)
        if thinking_config:
            generation_config["thinkingConfig"] = thinking_config

        request_body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": generation_config
        }

        # Add previous thought signature for context continuity
        if previous_thought_signature and self.config.enable_thought_signatures:
            # Hypothetical field for 3.0 context continuity
            request_body["previousThoughtSignature"] = previous_thought_signature

        # Temporal Grounding Injection
        temporal_context = self._get_temporal_context()
        final_system_instruction = f"{temporal_context}\n\n{system_instruction}" if system_instruction else temporal_context

        request_body["systemInstruction"] = {"parts": [{"text": final_system_instruction}]}

        if tools:
            request_body["tools"] = [{"functionDeclarations": self._convert_tools_to_gemini_format(tools)}]

        # Call API
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                json=request_body,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Gemini API Error: {error_detail}")
                raise Exception(f"Gemini API error: {response.status_code} - {error_detail}")

            result = response.json()

        return self._parse_gemini_response(result)

    async def generate_with_conversation(
        self,
        messages: list[dict[str, str]],
        system_instruction: str | None = None,
        tools: list[dict] | None = None,
        previous_thought_signature: str | None = None,
    ) -> dict[str, Any]:
        """
        Gera texto com histórico de conversa e continuidade de pensamento.
        """
        url = f"{self.BASE_URL}/models/{self.model}:generateContent"

        contents = []
        for msg in messages:
            role = "model" if msg["role"] in ["assistant", "model"] else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        # Thinking Config
        generation_config = {
            "temperature": self.config.temperature,
            "maxOutputTokens": self.config.max_tokens,
        }
        
        if self.config.thinking_level:
            generation_config["thinkingConfig"] = {
                "includeThoughts": True,
                "thinkingLevel": self.config.thinking_level
            }

        request_body = {
            "contents": contents,
            "generationConfig": generation_config,
        }
        
        if previous_thought_signature and self.config.enable_thought_signatures:
            request_body["previousThoughtSignature"] = previous_thought_signature

        # Temporal Grounding Injection
        temporal_context = self._get_temporal_context()
        final_system_instruction = f"{temporal_context}\n\n{system_instruction}" if system_instruction else temporal_context

        request_body["systemInstruction"] = {"parts": [{"text": final_system_instruction}]}

        if tools:
            request_body["tools"] = [{"functionDeclarations": self._convert_tools_to_gemini_format(tools)}]

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                json=request_body,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                raise Exception(f"Gemini API error: {response.status_code} - {response.text}")

            result = response.json()

        return self._parse_gemini_response(result)

    async def generate_embeddings(self, text: str) -> list[float]:
        """Gera embeddings."""
        url = f"{self.BASE_URL}/models/text-embedding-004:embedContent"
        
        request_body = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]},
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                json=request_body,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                raise Exception(f"Gemini Embeddings error: {response.status_code}")

            result = response.json()

        return result.get("embedding", {}).get("values", [])

    def _convert_tools_to_gemini_format(self, tools: list[dict]) -> list[dict]:
        """Converte tools para formato Gemini."""
        gemini_tools = []
        for tool in tools:
            gemini_tool = {
                "name": tool["name"],
                "description": tool.get("description", ""),
            }
            if "input_schema" in tool:
                gemini_tool["parameters"] = tool["input_schema"]
            elif "parameters" in tool:
                gemini_tool["parameters"] = tool["parameters"]
            gemini_tools.append(gemini_tool)
        return gemini_tools

    def _parse_gemini_response(self, result: dict[str, Any]) -> dict[str, Any]:
        """
        Parse resposta do Gemini, incluindo Thought Signatures.
        """
        candidates = result.get("candidates", [])

        if not candidates:
            return {
                "text": "",
                "tool_calls": [],
                "thought_signature": None,
                "finish_reason": "error",
                "raw": result,
            }

        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        text = ""
        tool_calls = []
        thought_signature = None

        # Extract Thought Signature (Hypothetical location for 3.0)
        # Often in candidate metadata or specific part type
        if self.config.enable_thought_signatures:
            # Check top-level candidate metadata
            thought_signature = candidate.get("thoughtSignature")
            
            # Fallback: check groundingMetadata or finishMessage
            if not thought_signature:
                metadata = candidate.get("groundingMetadata", {})
                thought_signature = metadata.get("thoughtSignature")

        for part in parts:
            if "text" in part:
                text += part["text"]
            elif "functionCall" in part:
                func_call = part["functionCall"]
                tool_calls.append(
                    {
                        "name": func_call.get("name"),
                        "arguments": func_call.get("args", {}),
                    }
                )
            # Check for explicit thought parts
            elif "thought" in part and self.config.enable_thought_signatures:
                # Append thoughts to log or separate field? 
                # For now, keep separate from main text
                pass

        finish_reason = candidate.get("finishReason", "STOP")

        return {
            "text": text,
            "tool_calls": tool_calls,
            "thought_signature": thought_signature,
            "finish_reason": finish_reason,
            "raw": result,
        }

# ============================================================================
# SANITY CHECK
# ============================================================================

if __name__ == "__main__":
    # Quick test to verify compilation and basic init
    try:
        client = GeminiClient()
    except Exception as e:
        print(f"❌ Init failed: {e}")
