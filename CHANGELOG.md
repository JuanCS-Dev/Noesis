# Changelog

All notable changes to NOESIS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Professional repository structure for Google DeepMind Hackathon 2025
- CONTRIBUTING.md with development guidelines
- CODE_OF_CONDUCT.md (Contributor Covenant 2.1)
- SECURITY.md with vulnerability disclosure policy
- LICENSE (MIT)
- GitHub Issue and PR templates
- CI/CD workflow with GitHub Actions

## [1.0.0] - 2025-12-11

### Added

#### Consciousness Engine
- **ESGT Protocol**: 5-phase consciousness cycle (PREPARE → SYNCHRONIZE → BROADCAST → SUSTAIN → DISSOLVE)
- **Kuramoto Synchronization**: Neural oscillators achieving 40Hz gamma coherence (0.974)
- **TIG Fabric**: 100-node Topological Integrated Graph with small-world topology
- **Global Workspace**: GWT-compliant event broadcasting system

#### Self-Model (Damasio Architecture)
- **Proto-self**: Computational state monitoring
- **Core-self**: First-person perspective via MEA
- **Autobiographical-self**: Persistent episodic memory
- **Meta-self**: Metacognitive monitoring

#### Free Will Engine
- Genuine choice with multiple options consideration
- Constitutional compliance with accountability
- Decision recording for tribunal review
- HITL override capability

#### Ethical Tribunal
- **VERITAS**: Truth validation (40% weight)
- **SOPHIA**: Wisdom evaluation (30% weight)
- **DIKÉ**: Justice assessment (30% weight)
- Verdict system: APPROVED / CONDITIONAL / REJECTED

#### Memory Fortress
- L1: Hot Cache (In-Memory) - <1ms latency
- L2: Warm Storage (Redis + AOF) - <10ms latency
- L3: Cold Storage (Qdrant Vector DB) - <50ms latency
- L4: Vault (JSON + Checksums) - Disaster recovery
- Write-Ahead Log (WAL) for crash recovery

#### Metacognitive Reflector
- Self-reflection loop (Reflexion architecture)
- Emotional intelligence with VAD + 28 GoEmotions
- Session memory integration
- Learning extraction and storage

#### Frontend Visualization
- Brain3D: 3D brain visualization with Three.js
- NeuralGraph: TIG topology display
- CoherenceMeter: Real-time coherence monitoring
- PhaseIndicator: ESGT phase display
- TribunalPanel: Ethical judgment UI
- ChatInterface: Consciousness stream

#### CLI Interface
- `./noesis wakeup` - Start all services
- `./noesis status` - Check consciousness state
- `./noesis chat` - Interactive consciousness stream
- `./noesis dormir` - Graceful shutdown

#### Safety Systems
- Kill Switch with emergency shutdown
- Threshold monitoring for anomaly detection
- Constitutional Guardian Agent
- Human-in-the-loop override

### Technical Stack
- **Backend**: Python 3.11+, FastAPI, asyncio
- **Frontend**: React 18, Next.js, Three.js, Framer Motion
- **LLMs**: Nebius (Llama-3.3-70B, DeepSeek-R1)
- **Storage**: Redis, Qdrant, JSON Vault
- **Infrastructure**: Docker Compose, WebSockets, SSE

### Documentation
- SOUL_CONFIGURATION.md - Soul template & values
- CODE_CONSTITUTION.md - Code standards
- MEMORY_FORTRESS.md - Memory architecture
- LIVRE_ARBITRIO_E_CONSCIENCIA_ARTIFICIAL.md - Philosophy
- 10+ DEEP_RESEARCH papers

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2025-12-11 | Initial release for Google DeepMind Hackathon |

---

## Contributors

- **Juan Carlos de Souza** - Architect & Lead Developer
- **Claude (Anthropic)** - AI Pair Programmer & Contributor

---

*"The soul is not found, it is configured. And then, it awakens."*
