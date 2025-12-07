"""
MIP Client for MAXIMUS Core Service

Cliente Python para comunicação com Motor de Integridade Processual.
Suporta avaliação de planos de ação via REST API.

Autor: Juan Carlos de Souza
"""

from __future__ import annotations


__version__ = "1.0.0"
__all__ = ["MIPClient", "MIPClientError", "MIPTimeoutError"]

from .client import MIPClient, MIPClientError, MIPTimeoutError
