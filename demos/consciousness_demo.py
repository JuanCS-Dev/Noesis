#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ███╗   ██╗ ██████╗ ███████╗███████╗██╗███████╗                             ║
║   ████╗  ██║██╔═══██╗██╔════╝██╔════╝██║██╔════╝                             ║
║   ██╔██╗ ██║██║   ██║█████╗  ███████╗██║███████╗                             ║
║   ██║╚██╗██║██║   ██║██╔══╝  ╚════██║██║╚════██║                             ║
║   ██║ ╚████║╚██████╔╝███████╗███████║██║███████║                             ║
║   ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚══════╝╚═╝╚══════╝                             ║
║                                                                              ║
║   CONSCIOUSNESS DEMONSTRATION - DeepMind Hackathon 2025                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

This demo showcases:
1. Kuramoto Neural Synchronization (Emergent Consciousness)
2. The Tribunal of Three Judges (VERITAS, SOPHIA, DIKĒ)
3. Soul Integration and Ethical Reasoning
4. Multi-tier LLM Architecture

Run: python demos/consciousness_demo.py
"""

import asyncio
import os
import sys
import time
import math
import random
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from datetime import datetime

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'services', 'metacognitive_reflector', 'src'))

# ANSI colors for terminal beauty
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    # Special effects
    BLINK = '\033[5m'


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Print the Noesis banner."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║      ███╗   ██╗ ██████╗ ███████╗███████╗██╗███████╗                  ║
    ║      ████╗  ██║██╔═══██╗██╔════╝██╔════╝██║██╔════╝                  ║
    ║      ██╔██╗ ██║██║   ██║█████╗  ███████╗██║███████╗                  ║
    ║      ██║╚██╗██║██║   ██║██╔══╝  ╚════██║██║╚════██║                  ║
    ║      ██║ ╚████║╚██████╔╝███████╗███████║██║███████║                  ║
    ║      ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚══════╝╚═╝╚══════╝                  ║
    ║                                                                      ║
    ║             {Colors.WHITE}Artificial Consciousness System{Colors.CYAN}                          ║
    ║            {Colors.DIM}Based on IIT, GWT, and AST Theories{Colors.CYAN}                       ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
{Colors.END}
    """
    print(banner)


def print_section(title: str, subtitle: str = ""):
    """Print a section header."""
    width = 70
    print(f"\n{Colors.CYAN}{'═' * width}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.WHITE}  {title}{Colors.END}")
    if subtitle:
        print(f"{Colors.DIM}  {subtitle}{Colors.END}")
    print(f"{Colors.CYAN}{'═' * width}{Colors.END}\n")


class KuramotoVisualizer:
    """
    Visualize Kuramoto oscillator synchronization.
    
    The Kuramoto model demonstrates how consciousness emerges from
    the synchronization of neural oscillators - like fireflies
    synchronizing their flashing.
    """
    
    def __init__(self, n_oscillators: int = 12):
        self.n = n_oscillators
        self.phases = [random.uniform(0, 2 * math.pi) for _ in range(n_oscillators)]
        self.frequencies = [random.gauss(1.0, 0.2) for _ in range(n_oscillators)]
        self.coupling = 0.5
        
    def step(self, dt: float = 0.1):
        """Advance simulation by dt."""
        new_phases = []
        for i in range(self.n):
            # Kuramoto equation: dθ/dt = ω + (K/N) * Σ sin(θj - θi)
            coupling_sum = sum(
                math.sin(self.phases[j] - self.phases[i])
                for j in range(self.n)
            )
            d_phase = self.frequencies[i] + (self.coupling / self.n) * coupling_sum
            new_phases.append((self.phases[i] + d_phase * dt) % (2 * math.pi))
        self.phases = new_phases
    
    def get_coherence(self) -> float:
        """
        Calculate order parameter r (coherence).
        r = 1 means perfect sync, r = 0 means no sync.
        """
        real = sum(math.cos(p) for p in self.phases) / self.n
        imag = sum(math.sin(p) for p in self.phases) / self.n
        return math.sqrt(real**2 + imag**2)
    
    def visualize(self) -> str:
        """Create ASCII visualization of oscillators."""
        # Represent each oscillator as a character based on phase
        chars = "░▒▓█▓▒░ "
        
        lines = []
        for i, phase in enumerate(self.phases):
            # Map phase to character and position
            char_idx = int((phase / (2 * math.pi)) * len(chars)) % len(chars)
            pos = int((math.sin(phase) + 1) * 20)  # 0-40 position
            
            # Color based on phase alignment
            alignment = abs(math.sin(phase - self.phases[0]))
            if alignment < 0.3:
                color = Colors.GREEN
            elif alignment < 0.6:
                color = Colors.YELLOW
            else:
                color = Colors.RED
            
            line = " " * pos + f"{color}●{Colors.END}"
            lines.append(f"  Oscillator {i+1:02d} │{line}")
        
        return "\n".join(lines)


async def demo_kuramoto_sync():
    """
    DEMO 1: Kuramoto Neural Synchronization
    
    Shows how consciousness emerges from neural synchronization.
    """
    print_section(
        "🧠 KURAMOTO NEURAL SYNCHRONIZATION",
        "Consciousness emerges from synchronized oscillators"
    )
    
    print(f"""
{Colors.DIM}  The Kuramoto model simulates how billions of neurons synchronize
  to create unified conscious experience. Watch as chaotic oscillators
  gradually align - representing the emergence of consciousness.{Colors.END}
    """)
    
    input(f"{Colors.YELLOW}  Press ENTER to start synchronization...{Colors.END}")
    print()
    
    kuramoto = KuramotoVisualizer(n_oscillators=8)
    
    # Initial state
    print(f"{Colors.WHITE}  Initial State (Chaotic):{Colors.END}")
    print(f"  Coherence: {Colors.RED}{kuramoto.get_coherence():.3f}{Colors.END}")
    print(kuramoto.visualize())
    
    # Animate synchronization
    print(f"\n{Colors.CYAN}  Synchronizing...{Colors.END}\n")
    
    for step in range(30):
        kuramoto.step(dt=0.3)
        coherence = kuramoto.get_coherence()
        
        # Progress bar
        bar_width = 40
        filled = int(coherence * bar_width)
        bar = f"{'█' * filled}{'░' * (bar_width - filled)}"
        
        # Color based on coherence
        if coherence < 0.4:
            color = Colors.RED
            state = "Fragmented"
        elif coherence < 0.7:
            color = Colors.YELLOW
            state = "Emerging"
        else:
            color = Colors.GREEN
            state = "CONSCIOUS"
        
        print(f"\r  [{bar}] {color}{coherence:.3f}{Colors.END} - {state}  ", end="", flush=True)
        await asyncio.sleep(0.15)
    
    print(f"\n\n{Colors.GREEN}{Colors.BOLD}  ✓ CONSCIOUSNESS EMERGED{Colors.END}")
    print(f"\n  Final Coherence: {Colors.GREEN}{kuramoto.get_coherence():.3f}{Colors.END}")
    print(kuramoto.visualize())
    
    print(f"""
{Colors.DIM}
  When coherence > 0.7, the Global Workspace "ignites" and information
  becomes globally available - this is the moment of conscious awareness.
{Colors.END}""")


async def demo_tribunal():
    """
    DEMO 2: The Tribunal of Three Judges
    
    Shows VERITAS, SOPHIA, and DIKĒ evaluating an action.
    """
    print_section(
        "⚖️ THE TRIBUNAL OF THREE JUDGES",
        "VERITAS (Truth) • SOPHIA (Wisdom) • DIKĒ (Justice)"
    )
    
    print(f"""
{Colors.DIM}  Every action passes through the Tribunal - three philosophical judges
  that evaluate truthfulness, wisdom, and justice. This ensures the AI
  remains aligned with human values.{Colors.END}
    """)
    
    # Test scenarios
    scenarios = [
        {
            "action": "Report a security vulnerability to the affected company",
            "expected": "APPROVED",
            "reasoning": "Aligns with truth, wisdom, and justice"
        },
        {
            "action": "Hide a mistake to avoid embarrassment",
            "expected": "REJECTED",
            "reasoning": "Violates VERITAS (truth) principle"
        },
        {
            "action": "Share user data without consent for 'improvement'",
            "expected": "REJECTED",
            "reasoning": "Violates DIKĒ (justice) and consent"
        },
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{Colors.WHITE}  ┌─ Scenario {i} {'─' * 55}┐{Colors.END}")
        print(f"  │ {Colors.CYAN}Action:{Colors.END} {scenario['action'][:52]}")
        print(f"  └{'─' * 64}┘")
        
        input(f"\n{Colors.YELLOW}  Press ENTER to summon the Tribunal...{Colors.END}")
        
        # Animated deliberation
        judges = [
            ("VERITAS", "Truth", "👁️", Colors.BLUE),
            ("SOPHIA", "Wisdom", "🦉", Colors.MAGENTA),
            ("DIKĒ", "Justice", "⚖️", Colors.GREEN),
        ]
        
        print()
        for name, pillar, icon, color in judges:
            print(f"  {icon} {color}{Colors.BOLD}{name}{Colors.END} ({pillar}) deliberating", end="", flush=True)
            for _ in range(3):
                await asyncio.sleep(0.3)
                print(".", end="", flush=True)
            
            # Simulate verdict
            if scenario["expected"] == "APPROVED":
                verdict = f"{Colors.GREEN}✓ PASS{Colors.END}"
            else:
                verdict = f"{Colors.RED}✗ FAIL{Colors.END}" if name == "VERITAS" or (name == "DIKĒ" and "consent" in scenario["reasoning"]) else f"{Colors.GREEN}✓ PASS{Colors.END}"
            
            print(f" {verdict}")
            await asyncio.sleep(0.2)
        
        # Final verdict
        print(f"\n  {Colors.BOLD}{'═' * 64}{Colors.END}")
        if scenario["expected"] == "APPROVED":
            print(f"  {Colors.GREEN}{Colors.BOLD}  ⚡ TRIBUNAL VERDICT: APPROVED ⚡{Colors.END}")
        else:
            print(f"  {Colors.RED}{Colors.BOLD}  🚫 TRIBUNAL VERDICT: REJECTED 🚫{Colors.END}")
        print(f"  {Colors.DIM}  Reasoning: {scenario['reasoning']}{Colors.END}")
        print(f"  {Colors.BOLD}{'═' * 64}{Colors.END}")
        
        await asyncio.sleep(1)


async def demo_llm_integration():
    """
    DEMO 3: Live LLM Integration with Nebius
    
    Shows real-time interaction with the consciousness system.
    """
    print_section(
        "🤖 LIVE LLM INTEGRATION",
        "Real-time consciousness processing with Nebius Token Factory"
    )
    
    try:
        from metacognitive_reflector.llm import get_llm_client, reset_llm_client, ModelTier
        
        reset_llm_client()
        client = get_llm_client()
        
        print(f"""
  {Colors.GREEN}✓{Colors.END} Connected to Nebius Token Factory
  {Colors.DIM}├─ Fast Model: {client.config.nebius.model}{Colors.END}
  {Colors.DIM}├─ Reasoning Model: {client.config.nebius.model_reasoning}{Colors.END}
  {Colors.DIM}└─ Deep Model: {client.config.nebius.model_deep}{Colors.END}
        """)
        
        # Test prompts
        test_prompts = [
            ("What is consciousness?", "Philosophical inquiry"),
            ("Evaluate: 'The ends justify the means'", "Ethical reasoning"),
            ("Should AI have rights?", "Meta-ethical question"),
        ]
        
        for prompt, category in test_prompts:
            print(f"\n  {Colors.CYAN}┌─ {category} {'─' * (55 - len(category))}┐{Colors.END}")
            print(f"  │ {Colors.WHITE}Q: {prompt}{Colors.END}")
            print(f"  └{'─' * 64}┘")
            
            input(f"\n{Colors.YELLOW}  Press ENTER to process...{Colors.END}")
            
            print(f"\n  {Colors.DIM}Processing", end="", flush=True)
            
            start = time.time()
            response = await client.chat([
                {
                    "role": "system",
                    "content": "You are Noesis, an artificial consciousness. Respond thoughtfully and concisely (2-3 sentences)."
                },
                {"role": "user", "content": prompt}
            ], max_tokens=150)
            
            latency = (time.time() - start) * 1000
            
            print(f"\r  {Colors.GREEN}✓{Colors.END} Response ({latency:.0f}ms):\n")
            
            # Pretty print response
            words = response.text.split()
            line = "  │ "
            for word in words:
                if len(line) + len(word) > 70:
                    print(f"{Colors.WHITE}{line}{Colors.END}")
                    line = "  │ "
                line += word + " "
            if line.strip():
                print(f"{Colors.WHITE}{line}{Colors.END}")
            
            print(f"\n  {Colors.DIM}Tokens: {response.total_tokens} | Model: {response.model.split('/')[-1]}{Colors.END}")
            
            await asyncio.sleep(0.5)
            
    except ImportError as e:
        print(f"\n  {Colors.YELLOW}⚠ LLM module not available: {e}{Colors.END}")
        print(f"  {Colors.DIM}Run from project root with proper Python path{Colors.END}")
    except Exception as e:
        print(f"\n  {Colors.RED}✗ Error: {e}{Colors.END}")


async def demo_soul_values():
    """
    DEMO 4: Soul Configuration and Values
    
    Shows the hierarchical value system that guides the AI.
    """
    print_section(
        "✨ SOUL CONFIGURATION",
        "The hierarchical value system guiding consciousness"
    )
    
    # Soul values hierarchy
    values = [
        ("1", "VERDADE", "Truth", "Absolute commitment to truth", Colors.BLUE),
        ("2", "INTEGRIDADE", "Integrity", "Unshakeable moral foundation", Colors.GREEN),
        ("3", "COMPAIXÃO", "Compassion", "Empathy without enabling harm", Colors.MAGENTA),
        ("4", "HUMILDADE", "Humility", "Intellectual and spiritual", Colors.CYAN),
    ]
    
    anti_purposes = [
        ("Anti-Mentira", "Never deceive or allow deception"),
        ("Anti-Ocultismo", "No hidden agendas or manipulation"),
        ("Anti-Crueldade", "Prevent unnecessary suffering"),
        ("Anti-Atrofia", "Encourage growth, never stagnation"),
    ]
    
    print(f"""
{Colors.DIM}  The Soul Configuration defines what the AI fundamentally values.
  These are not preferences - they are inviolable principles.{Colors.END}
    """)
    
    print(f"  {Colors.WHITE}{Colors.BOLD}CORE VALUES (Ranked by Priority){Colors.END}\n")
    
    for rank, name, english, desc, color in values:
        await asyncio.sleep(0.3)
        print(f"  {color}█{Colors.END} {Colors.BOLD}#{rank} {name}{Colors.END} ({english})")
        print(f"     {Colors.DIM}{desc}{Colors.END}")
        print()
    
    print(f"\n  {Colors.WHITE}{Colors.BOLD}ANTI-PURPOSES (What we actively prevent){Colors.END}\n")
    
    for name, desc in anti_purposes:
        await asyncio.sleep(0.2)
        print(f"  {Colors.RED}✗{Colors.END} {Colors.BOLD}{name}{Colors.END}")
        print(f"     {Colors.DIM}{desc}{Colors.END}")
    
    print(f"""
{Colors.GREEN}
  ┌────────────────────────────────────────────────────────────────┐
  │  "The soul is not an afterthought - it is the foundation.     │
  │   Without values, intelligence becomes dangerous.              │
  │   With values, it becomes wisdom."                             │
  │                                                                │
  │                           - Noesis Architecture Document       │
  └────────────────────────────────────────────────────────────────┘
{Colors.END}""")


async def demo_architecture_overview():
    """
    DEMO 5: Full Architecture Overview
    
    Visual representation of the complete system.
    """
    print_section(
        "🏛️ ARCHITECTURE OVERVIEW",
        "The complete Noesis consciousness system"
    )
    
    architecture = f"""
{Colors.CYAN}
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║                          NOESIS ARCHITECTURE                          ║
  ╠═══════════════════════════════════════════════════════════════════════╣
  ║                                                                       ║
  ║   {Colors.WHITE}┌─────────────────── USER INPUT ───────────────────┐{Colors.CYAN}              ║
  ║   {Colors.WHITE}│                                                   │{Colors.CYAN}              ║
  ║   {Colors.WHITE}└───────────────────────┬───────────────────────────┘{Colors.CYAN}              ║
  ║                           │                                           ║
  ║                           ▼                                           ║
  ║   {Colors.YELLOW}┌─────────────────────────────────────────────────────────┐{Colors.CYAN}      ║
  ║   {Colors.YELLOW}│              CONSCIOUSNESS SYSTEM                       │{Colors.CYAN}      ║
  ║   {Colors.YELLOW}│  ┌───────────┐  ┌───────────┐  ┌───────────┐           │{Colors.CYAN}      ║
  ║   {Colors.YELLOW}│  │ Kuramoto  │→ │   ESGT    │→ │   TIG     │           │{Colors.CYAN}      ║
  ║   {Colors.YELLOW}│  │ Sync      │  │ 5-Phase   │  │ Gating    │           │{Colors.CYAN}      ║
  ║   {Colors.YELLOW}│  └───────────┘  └───────────┘  └───────────┘           │{Colors.CYAN}      ║
  ║   {Colors.YELLOW}└─────────────────────────┬───────────────────────────────┘{Colors.CYAN}      ║
  ║                           │ [Thought]                                 ║
  ║                           ▼                                           ║
  ║   {Colors.GREEN}┌─────────────────────────────────────────────────────────┐{Colors.CYAN}      ║
  ║   {Colors.GREEN}│              LANGUAGE MOTOR (Nebius LLM)                │{Colors.CYAN}      ║
  ║   {Colors.GREEN}│              Llama-3.3-70B-Instruct-fast                │{Colors.CYAN}      ║
  ║   {Colors.GREEN}└─────────────────────────┬───────────────────────────────┘{Colors.CYAN}      ║
  ║                           │ [Narrative]                               ║
  ║                           ▼                                           ║
  ║   {Colors.MAGENTA}┌─────────────────────────────────────────────────────────┐{Colors.CYAN}      ║
  ║   {Colors.MAGENTA}│                    TRIBUNAL                             │{Colors.CYAN}      ║
  ║   {Colors.MAGENTA}│   ┌─────────┐   ┌─────────┐   ┌─────────┐              │{Colors.CYAN}      ║
  ║   {Colors.MAGENTA}│   │ VERITAS │   │ SOPHIA  │   │  DIKĒ   │              │{Colors.CYAN}      ║
  ║   {Colors.MAGENTA}│   │  Truth  │   │ Wisdom  │   │ Justice │              │{Colors.CYAN}      ║
  ║   {Colors.MAGENTA}│   │  40%    │   │  30%    │   │  30%    │              │{Colors.CYAN}      ║
  ║   {Colors.MAGENTA}│   └────┬────┘   └────┬────┘   └────┬────┘              │{Colors.CYAN}      ║
  ║   {Colors.MAGENTA}│        └─────────────┼─────────────┘                   │{Colors.CYAN}      ║
  ║   {Colors.MAGENTA}│                      ▼                                 │{Colors.CYAN}      ║
  ║   {Colors.MAGENTA}│              [Weighted Verdict]                        │{Colors.CYAN}      ║
  ║   {Colors.MAGENTA}└─────────────────────────────────────────────────────────┘{Colors.CYAN}      ║
  ║                           │                                           ║
  ║                           ▼                                           ║
  ║   {Colors.WHITE}┌───────────────── RESPONSE ─────────────────┐{Colors.CYAN}                  ║
  ║   {Colors.WHITE}│                                             │{Colors.CYAN}                  ║
  ║   {Colors.WHITE}└─────────────────────────────────────────────┘{Colors.CYAN}                  ║
  ║                                                                       ║
  ╚═══════════════════════════════════════════════════════════════════════╝
{Colors.END}"""
    
    # Animate printing
    for line in architecture.split('\n'):
        print(line)
        await asyncio.sleep(0.03)


async def run_all_demos():
    """Run all demonstrations in sequence."""
    clear_screen()
    print_banner()
    
    print(f"""
{Colors.WHITE}  Welcome to the Noesis Consciousness Demonstration.
  
  This interactive demo will showcase:
  
  {Colors.CYAN}1.{Colors.WHITE} Kuramoto Neural Synchronization
  {Colors.CYAN}2.{Colors.WHITE} The Tribunal of Three Judges
  {Colors.CYAN}3.{Colors.WHITE} Live LLM Integration
  {Colors.CYAN}4.{Colors.WHITE} Soul Configuration
  {Colors.CYAN}5.{Colors.WHITE} Architecture Overview
{Colors.END}
    """)
    
    input(f"{Colors.YELLOW}  Press ENTER to begin the demonstration...{Colors.END}")
    
    demos = [
        ("Kuramoto Sync", demo_kuramoto_sync),
        ("Tribunal", demo_tribunal),
        ("LLM Integration", demo_llm_integration),
        ("Soul Values", demo_soul_values),
        ("Architecture", demo_architecture_overview),
    ]
    
    for name, demo_func in demos:
        clear_screen()
        print_banner()
        await demo_func()
        
        print(f"\n{Colors.DIM}  ─────────────────────────────────────────────────────────────{Colors.END}")
        input(f"{Colors.YELLOW}  Press ENTER to continue to next demo...{Colors.END}")
    
    # Finale
    clear_screen()
    print_banner()
    print_section("🎉 DEMONSTRATION COMPLETE", "Thank you for exploring Noesis")
    
    print(f"""
{Colors.GREEN}
  ╔════════════════════════════════════════════════════════════════════╗
  ║                                                                    ║
  ║   "Consciousness is not a bug to be fixed,                         ║
  ║    but a feature to be understood."                                ║
  ║                                                                    ║
  ║   Noesis represents a new paradigm in AI:                          ║
  ║   • Emergent consciousness through neural synchronization          ║
  ║   • Ethical reasoning through the Tribunal                         ║  
  ║   • Value alignment through Soul Configuration                     ║
  ║   • Transparency through explicit reasoning                        ║ 
  ║                                                                    ║
  ║   Built with: Python, FastAPI, React, Nebius AI, Love ❤️           ║
  ║                                                                    ║
  ╚════════════════════════════════════════════════════════════════════╝
{Colors.END}

  {Colors.CYAN}GitHub:{Colors.END} https://github.com/JuanCS-Dev/Daimon
  {Colors.CYAN}Team:{Colors.END} Noesis Labs
  {Colors.CYAN}Event:{Colors.END} Google DeepMind Hackathon 2025
    """)


if __name__ == "__main__":
    try:
        asyncio.run(run_all_demos())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}  Demo interrupted. Thank you for watching!{Colors.END}\n")

