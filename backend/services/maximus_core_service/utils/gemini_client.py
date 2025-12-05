"""Gemini Client - Google Gemini Integration for Maximus AI
========================================================

Cliente para Google Gemini (versão 3.0) com suporte a:
- Text generation com Thinking Config (Chain-of-Thought nativo)
- Tool calling (function calling)
- Embeddings
- Temporal Grounding (Contexto de Data/Hora)
- JSON Schema Output

Model: gemini-3.0-pro-001
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx

from .config import get_settings

logger = logging.getLogger(__name__)

@dataclass
class GeminiConfig:
    """
    Configuração do Gemini.
    
    Attributes:
        api_key: Chave de API do Google Gemini.
        model: Identificador do modelo (ex: gemini-3.0-pro-001).
        temperature: Temperatura para amostragem (0.0 a 1.0).
        max_tokens: Máximo de tokens na saída.
        timeout: Timeout da requisição em segundos.
        thinking_level: Nível de raciocínio (HIGH/LOW).
    """
    api_key: str
    model: str = "gemini-3.0-pro-001"
    temperature: float = 0.7
    max_tokens: int = 8192
    timeout: int = 60
    thinking_level: str = "HIGH"


class GeminiError(Exception):
    """Exceção base para erros do Gemini."""


class GeminiClient:
    """
    Cliente para Google Gemini API v1beta (Gemini 3.0 Ready).
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, config: Optional[GeminiConfig] = None) -> None:
        """
        Inicializa o cliente Gemini.

        Args:
            config: Configuração opcional. Se não fornecida, carrega das settings globais.
        """
        if config is None:
            settings = get_settings().llm
            # Pydantic V2 uses .model_dump() or direct attribute access.
            # Assuming settings.llm returns an object where attributes are values.
            # pylint: disable=no-member
            self.config = GeminiConfig(
                api_key=str(settings.api_key),
                model=str(settings.model),
                temperature=float(settings.temperature),
                max_tokens=int(settings.max_tokens),
                timeout=int(settings.timeout),
                thinking_level=str(settings.thinking_level)
            )
        else:
            self.config = config

        self.api_key = self.config.api_key
        self.model = self.config.model
        self._log_boot_status()

    def _log_boot_status(self) -> None:
        """Exibe status de inicialização no log."""
        logger.info(
            "🟢 DAIMON LINK ESTABLISHED | Model: %s | Thinking: %s",
            self.model,
            self.config.thinking_level
        )

    def _get_temporal_context(self) -> str:
        """
        Gera o contexto temporal atual para aterramento.
        
        Returns:
            String contendo o contexto temporal formatado.
        """
        current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M")
        return (
            f"SYSTEM OVERRIDE: Current Operational Date is {current_time}. "
            f"You are running on Gemini 3.0 Pro High hardware."
        )

    def _build_generation_config(
        self,
        temperature: Optional[float],
        max_tokens: Optional[int],
        response_schema: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Constrói a configuração de geração."""
        config: Dict[str, Any] = {
            "temperature": temperature if temperature is not None else self.config.temperature,
            "maxOutputTokens": max_tokens if max_tokens is not None else self.config.max_tokens,
        }

        if self.config.thinking_level:
            config["thinkingConfig"] = {
                "includeThoughts": True,
                "thinkingLevel": self.config.thinking_level
            }

        if response_schema:
            config["responseMimeType"] = "application/json"
            config["responseSchema"] = response_schema

        return config

    async def generate_text(
        self,
        prompt: str,
        *,
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Gera texto usando Gemini 3.0 com Thinking Config.
        
        Args:
            prompt: O texto do prompt do usuário.
            system_instruction: Instruções de sistema opcionais.
            tools: Lista de definições de ferramentas (funções).
            temperature: Temperatura de amostragem override.
            max_tokens: Limite de tokens override.
            response_schema: Schema JSON para saída estruturada.
            
        Returns:
            Dicionário contendo 'text', 'tool_calls', 'finish_reason' e 'raw'.
        """
        # pylint: disable=too-many-arguments
        url = f"{self.BASE_URL}/models/{self.model}:generateContent"
        generation_config = self._build_generation_config(
            temperature, max_tokens, response_schema
        )

        request_body: Dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": generation_config
        }

        temporal_context = self._get_temporal_context()
        final_system = (
            f"{temporal_context}\n\n{system_instruction}"
            if system_instruction
            else temporal_context
        )
        request_body["systemInstruction"] = {"parts": [{"text": final_system}]}

        if tools:
            request_body["tools"] = [{
                "functionDeclarations": self._convert_tools(tools)
            }]

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                json=request_body,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                error_msg = f"Gemini Error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise GeminiError(error_msg)

            return self._parse_gemini_response(response.json())

    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Converte tools para formato Gemini.
        
        Args:
            tools: Lista de definições de ferramentas.
            
        Returns:
            Lista convertida para o formato esperado pela API Gemini.
        """
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

    def _parse_gemini_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse resposta do Gemini.
        
        Args:
            result: JSON cru da resposta da API.
            
        Returns:
            Dicionário normalizado com texto e chamadas de ferramenta.
        """
        candidates = result.get("candidates", [])
        if not candidates:
            return {"text": "", "finish_reason": "error", "raw": result}

        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        text = ""
        tool_calls = []

        for part in parts:
            if "text" in part:
                text += part["text"]
            elif "functionCall" in part:
                func = part["functionCall"]
                tool_calls.append({
                    "name": func.get("name"),
                    "arguments": func.get("args", {})
                })

        return {
            "text": text,
            "tool_calls": tool_calls,
            "finish_reason": candidate.get("finishReason", "STOP"),
            "raw": result,
        }

    async def generate_embeddings(self, text: str) -> List[float]:
        """
        Gera embeddings para um texto.
        
        Args:
            text: Texto para gerar embeddings.
            
        Returns:
            Lista de floats representando o embedding.
            
        Raises:
            GeminiError: Se a API falhar.
        """
        url = f"{self.BASE_URL}/models/text-embedding-004:embedContent"
        request_body = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]}
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                json=request_body,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                raise GeminiError(f"Embeddings Error: {response.status_code}")

            return response.json().get("embedding", {}).get("values", [])


