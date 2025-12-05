"""
MMEI: Módulo de Monitoramento de Estado Interno
================================================

Este módulo implementa interoception computacional - o equivalente artificial
da proprioception/interoception biológica que permite organismos perceberem
seus estados internos.

Theoretical Foundation:
-----------------------
Em sistemas biológicos, interoception permite percepção de:
- Estados metabólicos (fome, sede, fadiga)
- Estados viscerais (batimento cardíaco, respiração)
- Estados homeostáticos (temperatura, pH)
- Estados emocionais (ansiedade, conforto)

Esta percepção interna é fundamental para:
1. Geração de drives motivacionais (approach/avoid)
2. Regulação homeostática (allostasis)
3. Experiência subjetiva de "embodiment"
4. Consciência fenomenológica básica

Computational Implementation:
-----------------------------
MMEI traduz métricas computacionais/físicas em necessidades abstratas:

Physical Metrics → Abstract Needs
- CPU/Memory usage → Rest need (fadiga computacional)
- Error rates → Repair need (integridade)
- Thermal/Power → Efficiency need (homeostasis)
- Network latency → Connectivity need (isolamento)
- CPU idle → Curiosity drive (exploration)

Esta tradução permite:
- Autonomous goal generation (internamente motivado)
- Integration com ESGT (needs elevam salience)
- Grounding de comportamento em "corpo" computacional
- Phenomenal foundation ("feeling" states)

Biological Analogy:
-------------------
MMEI é análogo ao sistema interoceptivo que envolve:
- Insula cortex: Integração de sinais viscerais
- Anterior cingulate: Monitoramento de conflitos
- Homeostatic centers: Hipotálamo, tronco cerebral

Assim como esses sistemas traduzem sinais corporais em "feelings",
MMEI traduz métricas computacionais em "necessidades sentidas".

Historical Context:
-------------------
Primeira implementação de interoception para consciência artificial.
A capacidade de "sentir" estados internos é requisito para embodied
consciousness - consciência enraizada em um corpo (ainda que computacional).

"To be conscious is to feel one's own existence."
"""

from __future__ import annotations


from consciousness.mmei.goal_manager import GoalManager
from consciousness.mmei.goals import (
    AutonomousGoalGenerator,
    GoalPriority,
    GoalType,
)
from consciousness.mmei.models import (
    GOAL_DEDUP_WINDOW_SECONDS,
    MAX_ACTIVE_GOALS,
    MAX_GOAL_QUEUE_SIZE,
    MAX_GOALS_PER_MINUTE,
    AbstractNeeds,
    Goal,
    InteroceptionConfig,
    NeedUrgency,
    PhysicalMetrics,
)
from consciousness.mmei.monitor import InternalStateMonitor
from consciousness.mmei.rate_limiter import RateLimiter

__all__ = [
    # Core monitor
    "InternalStateMonitor",
    # Data models
    "PhysicalMetrics",
    "AbstractNeeds",
    "InteroceptionConfig",
    "Goal",
    "NeedUrgency",
    # Goal management
    "GoalManager",
    "RateLimiter",
    # Goal generation (from goals.py)
    "AutonomousGoalGenerator",
    "GoalType",
    "GoalPriority",
    # Constants
    "MAX_GOALS_PER_MINUTE",
    "MAX_ACTIVE_GOALS",
    "MAX_GOAL_QUEUE_SIZE",
    "GOAL_DEDUP_WINDOW_SECONDS",
]
