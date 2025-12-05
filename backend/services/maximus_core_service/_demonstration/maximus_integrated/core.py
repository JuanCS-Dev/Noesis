"""Maximus Core Integration.

Main MaximusIntegrated class integrating all AI components.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from agent_templates import AgentTemplates
from attention_system.attention_core import AttentionSystem
from autonomic_core.homeostatic_control import HomeostaticControlLoop
from autonomic_core.resource_analyzer import ResourceAnalyzer
from autonomic_core.resource_executor import ResourceExecutor
from autonomic_core.resource_planner import ResourcePlanner
from autonomic_core.system_monitor import SystemMonitor
from confidence_scoring import ConfidenceScoring
from ethical_guardian import EthicalGuardian
from ethical_tool_wrapper import EthicalToolWrapper
from gemini_client import GeminiClient, GeminiConfig
from governance import GovernanceConfig
from memory_system import MemorySystem
from neuromodulation import NeuromodulationController
from self_reflection import SelfReflection
from tool_orchestrator import ToolOrchestrator

from ..all_services_tools import AllServicesTools
from ..chain_of_thought import ChainOfThought
from ..rag_system import RAGSystem
from ..reasoning_engine import ReasoningEngine
from ..vector_db_client import VectorDBClient
from .neuromodulation_mixin import NeuromodulationMixin
from .predictive_coding_mixin import PredictiveCodingMixin
from .skill_learning_mixin import SkillLearningMixin


class MaximusIntegrated(
    NeuromodulationMixin,
    PredictiveCodingMixin,
    SkillLearningMixin,
):
    """Integrates and orchestrates all core components of the Maximus AI system.

    This class provides a unified interface to the entire Maximus AI, managing
    the interactions between its autonomic core, reasoning capabilities, memory,
    and tool-use functionalities.
    """

    def __init__(self):
        """Initialize all Maximus AI components and set up interconnections."""
        self._init_core_clients()
        self._init_neuromodulation()
        self._init_autonomic_core()
        self._init_attention_system()
        self._init_predictive_coding()
        self._init_skill_learning()
        self._init_other_components()
        self._init_ethical_stack()

    def _init_core_clients(self) -> None:
        """Initialize core clients and dependencies."""
        gemini_config = GeminiConfig(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model="gemini-1.5-flash",
            temperature=0.7,
            max_tokens=4096,
            timeout=60,
        )
        self.gemini_client = GeminiClient(gemini_config)
        self.vector_db_client = VectorDBClient()

    def _init_neuromodulation(self) -> None:
        """Initialize Neuromodulation System (FASE 5)."""
        self.neuromodulation = NeuromodulationController()

    def _init_autonomic_core(self) -> None:
        """Initialize Autonomic Core components."""
        self.system_monitor = SystemMonitor()
        self.resource_analyzer = ResourceAnalyzer()
        self.resource_planner = ResourcePlanner()
        self.resource_executor = ResourceExecutor()
        self.hcl = HomeostaticControlLoop(
            monitor=self.system_monitor,
            analyzer=self.resource_analyzer,
            planner=self.resource_planner,
            executor=self.resource_executor,
        )

    def _init_attention_system(self) -> None:
        """Initialize Attention System (FASE 0)."""
        base_foveal_threshold = 0.6
        self.attention_system = AttentionSystem(
            foveal_threshold=base_foveal_threshold, scan_interval=1.0
        )

    def _init_predictive_coding(self) -> None:
        """Initialize Predictive Coding Network (FASE 3)."""
        self.hpc_network = None
        self.predictive_coding_available = False
        try:
            from predictive_coding import HierarchicalPredictiveCodingNetwork

            self.hpc_network = HierarchicalPredictiveCodingNetwork(
                latent_dim=64, device="cpu"
            )
            self.predictive_coding_available = True
            print("[MAXIMUS] Predictive Coding Network initialized (FASE 3)")
        except ImportError as e:
            print(f"[MAXIMUS] Predictive Coding not available: {e}")

    def _init_skill_learning(self) -> None:
        """Initialize Skill Learning System (FASE 6)."""
        self.skill_learning = None
        self.skill_learning_available = False
        try:
            from skill_learning import SkillLearningController

            self.skill_learning = SkillLearningController(
                hsas_url=os.getenv("HSAS_SERVICE_URL", "http://localhost:8023"),
                timeout=30.0,
            )
            self.skill_learning_available = True
            print("[MAXIMUS] Skill Learning System initialized (FASE 6)")
        except Exception as e:
            print(f"[MAXIMUS] Skill Learning not available: {e}")

    def _init_other_components(self) -> None:
        """Initialize other core components."""
        self.memory_system = MemorySystem(vector_db_client=self.vector_db_client)
        self.rag_system = RAGSystem(vector_db_client=self.vector_db_client)
        self.agent_templates = AgentTemplates()
        self.all_services_tools = AllServicesTools(gemini_client=self.gemini_client)
        self.tool_orchestrator = ToolOrchestrator(gemini_client=self.gemini_client)
        self.chain_of_thought = ChainOfThought(gemini_client=self.gemini_client)
        self.reasoning_engine = ReasoningEngine(gemini_client=self.gemini_client)
        self.self_reflection = SelfReflection()
        self.confidence_scoring = ConfidenceScoring()

    def _init_ethical_stack(self) -> None:
        """Initialize Ethical AI Stack."""
        self.governance_config = GovernanceConfig()
        self.ethical_guardian = EthicalGuardian(
            governance_config=self.governance_config,
            enable_governance=True,
            enable_ethics=True,
            enable_fairness=True,
            enable_xai=True,
            enable_privacy=True,
            enable_fl=False,
            enable_hitl=True,
            enable_compliance=True,
        )
        self.ethical_wrapper = EthicalToolWrapper(
            ethical_guardian=self.ethical_guardian,
            enable_pre_check=True,
            enable_post_check=True,
            enable_audit=True,
        )
        self.tool_orchestrator.set_ethical_wrapper(self.ethical_wrapper)

    async def start_autonomic_core(self) -> None:
        """Start the Homeostatic Control Loop (HCL) for autonomic management."""
        await self.hcl.start()

    async def stop_autonomic_core(self) -> None:
        """Stop the Homeostatic Control Loop (HCL)."""
        await self.hcl.stop()

    async def process_query(
        self,
        query: str,
        user_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Process a natural language query through the integrated pipeline.

        Args:
            query: The natural language query from the user.
            user_context: Additional context provided by the user.

        Returns:
            A comprehensive response from Maximus.
        """
        print(f"[MaximusIntegrated] Processing query: {query}")
        start_time = datetime.now()

        # 1. Retrieve relevant information (RAG)
        retrieved_docs = await self.rag_system.retrieve(query)
        context = {
            "query": query,
            "user_context": user_context,
            "retrieved_docs": retrieved_docs,
        }

        # 2. Generate Chain of Thought
        cot_response = await self.chain_of_thought.generate_thought(query, context)
        context["cot_response"] = cot_response

        # 3. Reasoning Engine
        reasoning_output = await self.reasoning_engine.reason(query, context)
        initial_response = reasoning_output.get("response", "")
        tool_calls = reasoning_output.get("tool_calls", [])

        # 4. Execute tools if any
        tool_results = []
        if tool_calls:
            tool_results = await self.tool_orchestrator.execute_tools(tool_calls)
            context["tool_results"] = tool_results
            if tool_results:
                re_reason_prompt = (
                    f"Based on the initial query: {query}, "
                    f"and tool results: {tool_results}, refine the response."
                )
                reasoning_output = await self.reasoning_engine.reason(
                    re_reason_prompt, context
                )
                initial_response = reasoning_output.get("response", initial_response)

        # 5. Self-reflection and refinement
        reflection_output = await self.self_reflection.reflect_and_refine(
            {"output": initial_response, "tool_results": tool_results}, context
        )
        final_response = reflection_output.get("output", initial_response)

        # 6. Confidence Scoring
        confidence_score = await self.confidence_scoring.score(final_response, context)

        # 7. Store interaction in memory
        await self.memory_system.store_interaction(
            query, final_response, confidence_score
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "final_response": final_response,
            "confidence_score": confidence_score,
            "processing_time_seconds": duration,
            "timestamp": end_time.isoformat(),
            "raw_reasoning_output": reasoning_output,
            "tool_execution_results": tool_results,
            "reflection_notes": reflection_output.get("reflection_notes"),
        }

    async def get_system_status(self) -> dict[str, Any]:
        """Retrieve the current status of the integrated Maximus AI system."""
        hcl_status = await self.hcl.get_status()

        ethical_stats = self.ethical_guardian.get_statistics()
        wrapper_stats = self.ethical_wrapper.get_statistics()
        neuromod_state = self.get_neuromodulation_state()
        attention_stats = self.attention_system.get_performance_stats()

        return {
            "status": "online",
            "autonomic_core_status": hcl_status,
            "memory_system_status": "operational",
            "tool_orchestrator_status": "operational",
            "ethical_ai_status": {
                "guardian": ethical_stats,
                "wrapper": wrapper_stats,
                "average_overhead_ms": wrapper_stats.get("avg_overhead_ms", 0.0),
                "total_validations": ethical_stats.get("total_validations", 0),
                "approval_rate": ethical_stats.get("approval_rate", 0.0),
            },
            "neuromodulation_status": {
                "global_state": neuromod_state["global_state"],
                "modulated_parameters": neuromod_state["modulated_parameters"],
            },
            "attention_system_status": {
                "peripheral_detections": attention_stats["peripheral"][
                    "detections_total"
                ],
                "foveal_analyses": attention_stats["foveal"]["analyses_total"],
                "avg_analysis_time_ms": attention_stats["foveal"]["avg_analysis_time_ms"],
            },
            "predictive_coding_status": self.get_predictive_coding_state(),
            "skill_learning_status": self.get_skill_learning_state(),
            "last_update": datetime.now().isoformat(),
        }

    async def get_ethical_statistics(self) -> dict[str, Any]:
        """Get detailed ethical AI statistics."""
        return {
            "guardian": self.ethical_guardian.get_statistics(),
            "wrapper": self.ethical_wrapper.get_statistics(),
            "timestamp": datetime.now().isoformat(),
        }
