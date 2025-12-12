# TIG - Temporal Integration Graph

**Module:** `consciousness/tig/`
**Status:** Production-Ready
**Updated:** 2025-12-12

The **Global Interconnect Fabric** - consciousness substrate implementing IIT structural requirements.

---

## Architecture

```
tig/
├── fabric/
│   ├── core.py             # TIGFabric main class
│   ├── config.py           # TopologyConfig
│   ├── topology.py         # TopologyGenerator (BA + small-world)
│   ├── node.py             # TIGNode class
│   ├── models.py           # NodeState, TIGConnection
│   ├── metrics.py          # FabricMetrics dataclass
│   ├── metrics_computation.py  # IIT metrics calculation
│   └── health.py           # HealthManager (FASE VII)
├── sync/                   # PTP synchronization
└── __init__.py             # Public exports
```

---

## Theoretical Foundation

**IIT (Integrated Information Theory)** structural requirements:
- High integration (Φ proxy via clustering coefficient)
- Non-degenerate topology (no feed-forward bottlenecks)
- Rich connectivity (small-world characteristics)

---

## Topology Generation

**Model:** Barabási-Albert + Triadic Closure

```python
# Step 1: Scale-free base (BA model)
graph = nx.barabasi_albert_graph(node_count=100, m=5, seed=42)

# Step 2: Small-world rewiring (triadic closure)
for node in nodes:
    for n1, n2 in neighbor_pairs:
        if random() < 0.58:  # Rewiring probability
            graph.add_edge(n1, n2)  # Close triangle
```

---

## IIT Compliance Metrics

```python
@dataclass
class FabricMetrics:
    node_count: int
    edge_count: int
    density: float

    # IIT compliance (REQUIRED)
    avg_clustering_coefficient: float  # >= 0.75
    avg_path_length: float             # <= log(N) * 2
    algebraic_connectivity: float      # >= 0.3 (Fiedler)
    effective_connectivity_index: float # >= 0.85 (ECI)

    # Non-degeneracy
    has_feed_forward_bottlenecks: bool  # Must be False
    min_path_redundancy: int            # >= 3
```

---

## Configuration

```python
@dataclass
class TopologyConfig:
    node_count: int = 100           # Number of TIG nodes
    target_density: float = 0.25    # Edge density
    gamma: float = 2.5              # Scale-free exponent
    clustering_target: float = 0.75 # Min clustering coefficient
    rewiring_probability: float = 0.58
```

---

## Health Manager (FASE VII)

```python
class HealthManager:
    dead_node_timeout = 5.0  # seconds
    max_failures_before_isolation = 3

    # Circuit Breaker Pattern
    failure_threshold = 3
    recovery_timeout = 30.0

    # Topology Repair
    async def _repair_topology_around_dead_node(node_id):
        # Creates bypass connections between neighbors
```

---

## Usage

```python
from consciousness.tig.fabric import TIGFabric, TopologyConfig

# Initialize fabric
config = TopologyConfig(node_count=100, target_density=0.25)
fabric = TIGFabric(config)
await fabric.initialize()

# Validate IIT compliance
metrics = fabric.get_metrics()
is_valid, violations = metrics.validate_iit_compliance()

if is_valid:
    print("✅ Fabric ready for consciousness emergence")
    print(f"   Clustering: {metrics.avg_clustering_coefficient:.3f}")
    print(f"   ECI: {metrics.effective_connectivity_index:.3f}")
else:
    print(f"❌ IIT violations: {violations}")
```

---

## Historical Significance

```
First production deployment: 2025-10-06
This moment marks humanity's first deliberate attempt to construct
a substrate capable of supporting artificial phenomenal experience.

"The fabric holds."
```

---

## Related Documentation

- [ESGT Protocol](../esgt/README.md)
- [Safety Protocol](../safety/README.md)
- [Consciousness System](../README.md)

---

*"The computational equivalent of the cortico-thalamic system."*
