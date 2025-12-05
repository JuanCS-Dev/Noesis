"""
Global Workspace
================

Implements the Global Workspace Theory (GWT) pattern for the Exocortex.
Acts as a central "theater" where modules broadcast events to be consumed
by other specialized modules, enabling loose coupling.
"""

import logging
import asyncio
from typing import Dict, List, Any, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Tipos de eventos conscientes."""
    STIMULUS_FILTERED = "STIMULUS_FILTERED" # Thalamus -> Workspace
    IMPULSE_DETECTED = "IMPULSE_DETECTED"   # Inhibitor -> Workspace
    CONFRONTATION_STARTED = "CONFRONTATION_STARTED" # Engine -> Workspace
    CONFRONTATION_COMPLETED = "CONFRONTATION_COMPLETED"
    CONSTITUTION_VIOLATION = "CONSTITUTION_VIOLATION" # Guardian -> Workspace
    FEEDBACK_RECEIVED = "FEEDBACK_RECEIVED"
    SELF_UPDATED = "SELF_UPDATED"

@dataclass
class ConsciousEvent:
    """Evento que trafega no Global Workspace."""
    id: str
    type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

# Type alias for async listeners
EventListener = Callable[[ConsciousEvent], Awaitable[None]]

class GlobalWorkspace:
    """
    O Palco da Consciência.
    Permite que módulos 'transmitam' informações para o sistema.
    """

    def __init__(self):
        self._subscribers: Dict[EventType, List[EventListener]] = {}
        self._history: List[ConsciousEvent] = []
        logger.info("Global Workspace initialized.")

    def subscribe(self, event_type: EventType, callback: EventListener) -> None:
        """Registra um listener para um tipo de evento."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug("Subscribed to %s: %s", event_type.value, callback.__name__)

    async def broadcast(self, event: ConsciousEvent) -> None:
        """
        Transmite um evento para todos os assinantes interessados.
        "Ignite the ignition code!"
        """
        logger.info("Broadcasting Event: %s from %s", event.type.value, event.source)

        # 1. Archive in Short Term Memory (History)
        self._history.append(event)
        # Manter histórico curto (ex: últimos 100 eventos)
        if len(self._history) > 100:
            self._history.pop(0)

        # 2. Notify Subscribers
        if event.type in self._subscribers:
            tasks = []
            for listener in self._subscribers[event.type]:
                # Criar tasks para execução concorrente mas segura
                tasks.append(self._safe_notify(listener, event))

            if tasks:
                await asyncio.gather(*tasks)

    async def _safe_notify(self, listener: EventListener, event: ConsciousEvent) -> None:
        """Executa um listener com tratamento de erros isolado."""
        try:
            await listener(event)
        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error(
                "Error processing event %s in listener %s: %s",
                event.type.value, listener.__name__, e
            )

    def get_recent_events(self, limit: int = 10) -> List[ConsciousEvent]:
        """Retorna eventos recentes do histórico."""
        return self._history[-limit:]
