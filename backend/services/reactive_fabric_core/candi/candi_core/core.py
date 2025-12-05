"""
Main CANDI Core Class.

Central Analysis & Decision Intelligence engine.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..attribution_engine import AttributionEngine
from ..forensic_analyzer import ForensicAnalyzer
from ..threat_intelligence import ThreatIntelligence
from .classification import ClassificationMixin
from .incidents import IncidentMixin
from .models import AnalysisResult, Incident, ThreatLevel
from .recommendations import RecommendationMixin

logger = logging.getLogger(__name__)


class CANDICore(ClassificationMixin, RecommendationMixin, IncidentMixin):
    """
    CANDI Core - Central Analysis & Decision Intelligence.

    Pipeline:
    1. Receive event from honeypot
    2. Forensic analysis
    3. Threat intelligence correlation
    4. Attribution scoring
    5. Generate recommendations
    6. Request HITL decision if needed
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize CANDI Core.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Analysis engines
        self.forensic_analyzer = ForensicAnalyzer()
        self.attribution_engine = AttributionEngine()
        self.threat_intel = ThreatIntelligence()

        # Incident tracking
        self.active_incidents: Dict[str, Incident] = {}
        self.incident_counter = 0

        # Analysis queue
        self.analysis_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self.workers: List[asyncio.Task[None]] = []
        self._running = False

        # Callbacks
        self.analysis_callbacks: List[Callable[..., Any]] = []
        self.hitl_request_callback: Optional[Callable[..., Any]] = None

        # Statistics
        self.stats: Dict[str, Any] = {
            "total_analyzed": 0,
            "by_threat_level": {level.name: 0 for level in ThreatLevel},
            "hitl_requests": 0,
            "active_incidents": 0,
            "avg_processing_time_ms": 0,
        }

    async def start(self, num_workers: int = 4) -> None:
        """
        Start CANDI analysis workers.

        Args:
            num_workers: Number of parallel analysis workers
        """
        if self._running:
            logger.warning("CANDI Core already running")
            return

        self._running = True

        # Initialize analysis engines
        await self.forensic_analyzer.initialize()
        await self.attribution_engine.initialize()
        await self.threat_intel.initialize()

        # Start worker tasks
        for i in range(num_workers):
            worker = asyncio.create_task(self._analysis_worker(f"worker-{i}"))
            self.workers.append(worker)

        logger.info("CANDI Core started with %d workers", num_workers)

    async def stop(self) -> None:
        """Stop CANDI Core."""
        self._running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        await asyncio.gather(*self.workers, return_exceptions=True)

        logger.info("CANDI Core stopped")

    async def analyze_honeypot_event(
        self,
        event: Dict[str, Any],
    ) -> AnalysisResult:
        """
        Analyze event from honeypot.

        Args:
            event: Event data from honeypot

        Returns:
            Complete analysis result
        """
        start_time = datetime.now()

        # Generate analysis ID
        analysis_id = self._generate_analysis_id(event)

        logger.info(
            "Starting analysis %s for event from %s",
            analysis_id,
            event.get('source_ip'),
        )

        # Step 1: Forensic Analysis
        forensic_report = await self.forensic_analyzer.analyze(event)

        # Step 2: Threat Intelligence Correlation
        threat_intel_report = await self.threat_intel.correlate(forensic_report)

        # Step 3: Attribution
        attribution = await self.attribution_engine.attribute(
            forensic_report,
            threat_intel_report,
        )

        # Step 4: Classify Threat Level
        threat_level = self._classify_threat_level(
            forensic_report,
            threat_intel_report,
            attribution,
        )

        # Step 5: Extract IOCs and TTPs
        iocs = self._extract_iocs(forensic_report, threat_intel_report)
        ttps = self._map_to_mitre_attack(forensic_report)

        # Step 6: Generate Recommendations
        recommendations = self._generate_recommendations(
            threat_level,
            attribution,
            forensic_report,
        )

        # Step 7: Determine if HITL needed
        requires_hitl = self._requires_hitl_decision(threat_level, attribution)

        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        # Create analysis result
        result = AnalysisResult(
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            honeypot_id=event.get('honeypot_id', 'unknown'),
            source_ip=event.get('source_ip', 'unknown'),
            threat_level=threat_level,
            forensic_report=forensic_report,
            threat_intel=threat_intel_report,
            attribution=attribution,
            iocs=iocs,
            ttps=ttps,
            recommended_actions=recommendations,
            requires_hitl=requires_hitl,
            confidence_score=attribution.confidence / 100.0,
            processing_time_ms=processing_time,
        )

        # Update statistics
        self._update_stats(result)

        # Create or update incident
        if threat_level.value >= ThreatLevel.TARGETED.value:
            incident = self._create_or_update_incident(event, result)
            result.incident_id = incident.incident_id

        # Request HITL if needed
        if requires_hitl and self.hitl_request_callback:
            await self.hitl_request_callback(result)

        # Notify callbacks
        for callback in self.analysis_callbacks:
            try:
                await callback(result)
            except Exception as e:
                logger.error("Analysis callback error: %s", e)

        logger.info(
            "Analysis %s complete: %s (confidence: %.2f, time: %dms)",
            analysis_id,
            threat_level.name,
            result.confidence_score,
            processing_time,
        )

        return result

    async def submit_for_analysis(self, event: Dict[str, Any]) -> None:
        """
        Submit event to analysis queue.

        Args:
            event: Event data from honeypot
        """
        await self.analysis_queue.put(event)

    async def _analysis_worker(self, worker_id: str) -> None:
        """
        Analysis worker - processes events from queue.

        Args:
            worker_id: Worker identifier
        """
        logger.info("Analysis worker %s started", worker_id)

        while self._running:
            try:
                # Get event from queue (timeout to allow checking _running)
                try:
                    event = await asyncio.wait_for(
                        self.analysis_queue.get(),
                        timeout=1.0,
                    )
                except asyncio.TimeoutError:
                    continue

                # Analyze event
                try:
                    await self.analyze_honeypot_event(event)
                except Exception as e:
                    logger.error("Worker %s analysis error: %s", worker_id, e)
                finally:
                    self.analysis_queue.task_done()

            except Exception as e:
                logger.error("Worker %s error: %s", worker_id, e)

        logger.info("Analysis worker %s stopped", worker_id)

    def _generate_analysis_id(self, event: Dict[str, Any]) -> str:
        """Generate unique analysis ID."""
        data = f"{event.get('source_ip')}{event.get('timestamp')}{datetime.now()}"
        return f"CANDI-{hashlib.sha256(data.encode()).hexdigest()[:16]}"

    def _update_stats(self, result: AnalysisResult) -> None:
        """Update CANDI statistics."""
        self.stats["total_analyzed"] += 1
        self.stats["by_threat_level"][result.threat_level.name] += 1

        if result.requires_hitl:
            self.stats["hitl_requests"] += 1

        # Update average processing time
        total = self.stats["total_analyzed"]
        current_avg = self.stats["avg_processing_time_ms"]
        new_avg = ((current_avg * (total - 1)) + result.processing_time_ms) / total
        self.stats["avg_processing_time_ms"] = int(new_avg)

    def register_analysis_callback(self, callback: Callable[..., Any]) -> None:
        """Register callback for analysis completion."""
        self.analysis_callbacks.append(callback)

    def register_hitl_callback(self, callback: Callable[..., Any]) -> None:
        """Register callback for HITL requests."""
        self.hitl_request_callback = callback

    def get_stats(self) -> Dict[str, Any]:
        """Get CANDI statistics."""
        return {
            **self.stats,
            "queue_size": self.analysis_queue.qsize(),
            "workers_active": len(self.workers),
        }
