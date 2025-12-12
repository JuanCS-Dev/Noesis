# Safety Protocol

**Module:** `consciousness/safety/`
**Status:** Production-Ready
**Updated:** 2025-12-12

Unified safety coordinator integrating ThresholdMonitor, AnomalyDetector, and KillSwitch.

---

## Architecture

```
safety/
├── protocol.py             # ConsciousnessSafetyProtocol (main)
├── kill_switch.py          # KillSwitch (<1s response)
├── threshold_monitor.py    # Hard limit monitoring
├── anomaly_detector.py     # Statistical anomaly detection
├── thresholds.py           # SafetyThresholds dataclass
├── models.py               # SafetyViolation, etc.
├── enums.py                # ShutdownReason, ThreatLevel
└── component_health.py     # ComponentHealthMixin
```

---

## Components

| Component | Function |
|-----------|----------|
| **ThresholdMonitor** | Hard limits (ESGT freq, arousal, memory) |
| **AnomalyDetector** | Statistical detection (Z-score, trend) |
| **KillSwitch** | Emergency shutdown (<1s GUARANTEED) |

---

## Kill Switch

**CRITICAL:** <1s response time GUARANTEED

```python
class KillSwitch:
    """
    NO async operations
    NO external dependencies
    """

    def trigger(reason: ShutdownReason, context: dict):
        # 1. Capture state snapshot (100ms)
        # 2. Stop consciousness components (500ms)
        # 3. Generate incident report (200ms)
        # 4. Save report to disk (100ms)
```

### Shutdown Reasons

```python
class ShutdownReason(Enum):
    MANUAL = "manual"              # Operator command
    THRESHOLD = "threshold"        # Threshold violation
    ANOMALY = "anomaly"            # Anomaly detected
    ETHICAL = "ethical"            # Ethical violation
    SELF_MODIFICATION = "self_modification"  # ZERO TOLERANCE
```

---

## Safety Thresholds

```python
@dataclass
class SafetyThresholds:
    esgt_frequency_max_hz: float = 10.0
    arousal_max: float = 0.95
    goal_spam_threshold: int = 100
    self_modification_attempts_max: int = 0  # ZERO TOLERANCE
    memory_usage_max_gb: float = 4.0
    cpu_usage_max_percent: float = 90.0
```

---

## Threat Levels

```python
class ThreatLevel(Enum):
    NONE = 0      # Normal operation
    LOW = 1       # Minor anomaly
    MEDIUM = 2    # Significant anomaly
    HIGH = 3      # Critical threat
    CRITICAL = 4  # Emergency shutdown required
```

---

## Degradation Levels

```
Level 0: Normal operation
Level 1: Minor degradation (increased monitoring)
Level 2: Major degradation (reduced functionality)
Level 3: Critical (emergency shutdown imminent)
```

---

## Usage

```python
from consciousness.safety.protocol import ConsciousnessSafetyProtocol
from consciousness.safety.thresholds import SafetyThresholds

# Initialize
thresholds = SafetyThresholds(
    esgt_frequency_max_hz=10.0,
    arousal_max=0.95
)
safety = ConsciousnessSafetyProtocol(consciousness_system, thresholds)

# Start monitoring
await safety.start_monitoring()

# Register violation callback
safety.on_violation = lambda v: logger.warning(f"Violation: {v}")

# Manual emergency shutdown
await safety.execute_emergency_shutdown(reason=ShutdownReason.MANUAL)
```

---

## Monitoring Loop

```python
async def _monitoring_loop(self) -> None:
    """Main monitoring loop (1 Hz)."""
    while self.monitoring_active:
        # Check thresholds
        violations = self.threshold_monitor.check_all()

        # Check anomalies
        anomalies = self.anomaly_detector.detect()

        # Handle violations
        for v in violations:
            if v.severity >= ThreatLevel.CRITICAL:
                await self.execute_emergency_shutdown(ShutdownReason.THRESHOLD)
            else:
                await self._handle_violation(v)

        await asyncio.sleep(1.0)
```

---

## Related Documentation

- [ESGT Protocol](../esgt/README.md)
- [Consciousness System](../README.md)

---

*"Safety is not negotiable. <1s kill switch response is GUARANTEED."*
