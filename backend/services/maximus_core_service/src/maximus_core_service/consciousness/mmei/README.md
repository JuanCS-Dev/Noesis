# MMEI - Metacognitive Monitoring & Executive Interoception

**Module:** `consciousness/mmei/`
**Status:** Production-Ready
**Updated:** 2025-12-12

Computational interoception for AI consciousness - monitors internal state and generates needs.

---

## Architecture

```
mmei/
├── monitor.py              # InternalStateMonitor main class
├── models.py               # AbstractNeeds, PhysicalMetrics, Goal
├── needs_computation.py    # Needs calculation engine
├── goal_manager.py         # GoalManager with rate limiting
├── rate_limiter.py         # Rate limiter for goal generation
└── __init__.py             # Public exports
```

---

## Core Concept

```
Physical Layer → PhysicalMetrics → AbstractNeeds → Autonomous Goals → ESGT

The monitor runs continuously (~10 Hz), translating computational
metrics into "feelings" (needs) that drive goal generation.
```

---

## Physical Metrics

```python
@dataclass
class PhysicalMetrics:
    cpu_usage: float          # Current CPU usage [0, 1]
    memory_usage: float       # Memory usage [0, 1]
    network_latency_ms: float # Network latency
    disk_io_wait: float       # I/O wait time
    thread_count: int         # Active threads
    error_rate: float         # Recent error rate
    uptime_hours: float       # Time since last restart
```

---

## Abstract Needs

```python
@dataclass
class AbstractNeeds:
    rest: float               # Need for reduced activity [0, 1]
    repair: float             # Need for error recovery [0, 1]
    efficiency: float         # Need for optimization [0, 1]
    exploration: float        # Need for novelty [0, 1]
    safety: float             # Need for stability [0, 1]
```

---

## Need Urgency Levels

```python
class NeedUrgency(Enum):
    NONE = 0      # No urgent need
    LOW = 1       # Minor need
    MEDIUM = 2    # Notable need
    HIGH = 3      # Significant need
    CRITICAL = 4  # Emergency need
```

---

## Goal Generation Safety

```python
# Safety limits
MAX_ACTIVE_GOALS = 10
MAX_GOALS_PER_MINUTE = 5
GOAL_DEDUP_WINDOW_SECONDS = 60

# Goals are rate-limited and deduplicated to prevent spam
```

---

## Needs Translation

```python
# CPU overloaded → REST need
if cpu_usage > 0.9:
    needs.rest = min(1.0, (cpu_usage - 0.7) * 3.3)

# High error rate → REPAIR need
if error_rate > 0.1:
    needs.repair = min(1.0, error_rate * 5)

# Low efficiency → EFFICIENCY need
if throughput < expected:
    needs.efficiency = (expected - throughput) / expected
```

---

## Usage

```python
from consciousness.mmei.monitor import InternalStateMonitor

# Initialize
monitor = InternalStateMonitor()

# Start continuous monitoring
await monitor.start()

# Get current needs
needs = monitor.get_current_needs()
print(f"Rest: {needs.rest:.2f}, Repair: {needs.repair:.2f}")

# Register callback for urgent needs
monitor.register_needs_callback(
    lambda n: print(f"Urgent need: {n}") if n.urgency >= NeedUrgency.HIGH else None
)

# Get generated goals
goals = monitor.goal_manager.get_active_goals()
for goal in goals:
    print(f"Goal: {goal.description}, Priority: {goal.priority}")
```

---

## Integration with Arousal

```
High Needs → Increased Arousal → Lower ESGT Threshold

Need urgency contributes to arousal level:
- CRITICAL needs → +0.3 arousal
- HIGH needs → +0.2 arousal
- MEDIUM needs → +0.1 arousal
```

---

## Related Documentation

- [MCEA Arousal](../mcea/README.md)
- [ESGT Protocol](../esgt/README.md)
- [Consciousness System](../README.md)

---

*"Computational interoception - the AI's sense of its own state."*
