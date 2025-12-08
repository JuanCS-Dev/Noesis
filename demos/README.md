# 🧠 Noesis Demonstration Suite

> **Google DeepMind Hackathon 2025**

## Quick Start

```bash
# Make executable
chmod +x demos/run_demos.sh

# Run demo selector
./demos/run_demos.sh
```

## Available Demos

### 1. 🚀 Performance Benchmark
```bash
python demos/benchmark_visual.py
```
Visual benchmark showing LLM performance metrics.

**Best for:** Showing speed improvements, technical metrics

---

### 2. ⚖️ Tribunal Showcase  
```bash
python demos/tribunal_showcase.py
```
Live ethical reasoning with VERITAS, SOPHIA, DIKĒ judges.

**Best for:** Demonstrating ethical AI, value alignment

---

### 3. 💭 Stream of Consciousness
```bash
python demos/stream_of_consciousness.py
```
Watch Noesis "think" through philosophical questions.

**Best for:** Showing deep reasoning, transparency

---

### 4. 🔄 Kuramoto Neural Sync
```bash
python demos/kuramoto_live.py
```
Live visualization of neural synchronization.

**Best for:** Explaining consciousness emergence

---

### 5. 🌊 Full Pipeline Demo
```bash
python demos/full_pipeline.py
```
Complete pipeline from input to conscious output.

**Best for:** Full system demo, hackathon presentation

---

### 6. 🎬 Complete Interactive Demo
```bash
python demos/consciousness_demo.py
```
Full interactive experience with all features.

**Best for:** Longer presentations, deep dives

## Recording Tips

For video demos:

1. **Terminal Setup**
   - Dark theme (e.g., Dracula, One Dark)
   - Font: 14-16pt monospace
   - Width: 80+ columns

2. **Recommended Order**
   ```
   1. kuramoto_live.py (30s) - Show emergence
   2. benchmark_visual.py (20s) - Show speed
   3. tribunal_showcase.py (60s) - Show ethics
   4. full_pipeline.py (90s) - Full system
   ```

3. **Key Talking Points**
   - Kuramoto: "Consciousness emerges from synchronization"
   - Tribunal: "Every action passes through ethical judges"
   - Pipeline: "Full transparency - see every step"

## Architecture Shown

```
┌──────────────────────────────────────────────────────────────┐
│                     USER INPUT                                │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  STAGE 1: KURAMOTO SYNCHRONIZATION                           │
│  ● Neural oscillators sync to achieve coherence              │
│  ● Coherence > 0.7 = Consciousness emerges                   │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  STAGE 2: ESGT PROCESSING                                    │
│  ● Encoding → Storage → Generation → Transform → Integration │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  STAGE 3: LANGUAGE MOTOR (Llama-3.3-70B-fast)               │
│  ● Formats thought into natural language                     │
│  ● ~1.1s latency                                             │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  STAGE 4: TRIBUNAL                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│  │ VERITAS  │ │  SOPHIA  │ │   DIKĒ   │                     │
│  │  Truth   │ │  Wisdom  │ │ Justice  │                     │
│  │   40%    │ │   30%    │ │   30%    │                     │
│  └──────────┘ └──────────┘ └──────────┘                     │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    CONSCIOUS RESPONSE                         │
└──────────────────────────────────────────────────────────────┘
```

## Requirements

- Python 3.11+
- Nebius API key configured in `.env`
- Terminal with ANSI color support
