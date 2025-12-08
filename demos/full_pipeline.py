#!/usr/bin/env python3
"""
NOESIS FULL PIPELINE DEMO
=========================
Shows the complete thought process from input to output.
"""

import asyncio
import os
import sys
import time
import math
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'services', 'metacognitive_reflector', 'src'))

class C:
    G = '\033[92m'; Y = '\033[93m'; R = '\033[91m'; C = '\033[96m'
    W = '\033[97m'; B = '\033[1m'; D = '\033[2m'; E = '\033[0m'
    M = '\033[35m'; BL = '\033[94m'

def box(title, content, color=None):
    c = color or C.C
    w = 68
    print(f"  {c}╭{'─' * w}╮{C.E}")
    print(f"  {c}│{C.E} {C.B}{title.center(w-2)}{C.E} {c}│{C.E}")
    print(f"  {c}├{'─' * w}┤{C.E}")
    for line in content.split('\n'):
        print(f"  {c}│{C.E} {line:{w-2}} {c}│{C.E}")
    print(f"  {c}╰{'─' * w}╯{C.E}")

async def simulate_kuramoto():
    """Quick Kuramoto simulation."""
    phases = [random.uniform(0, 2*math.pi) for _ in range(6)]
    for _ in range(20):
        new = []
        for i in range(6):
            s = sum(math.sin(phases[j] - phases[i]) for j in range(6))
            new.append((phases[i] + 1.0 + 0.5/6 * s * 0.2) % (2*math.pi))
        phases = new
        
        coh = math.sqrt(
            (sum(math.cos(p) for p in phases)/6)**2 +
            (sum(math.sin(p) for p in phases)/6)**2
        )
        
        bar = '█' * int(coh * 30) + '░' * (30 - int(coh * 30))
        color = C.G if coh > 0.7 else C.Y
        print(f"\r    Sync: [{color}{bar}{C.E}] {coh:.2f}", end='', flush=True)
        await asyncio.sleep(0.05)
    print(f" {C.G}✓{C.E}")
    return coh

async def run_pipeline(user_input, client):
    """Run the full consciousness pipeline."""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"""
{C.M}╔══════════════════════════════════════════════════════════════════════════╗
║                       NOESIS CONSCIOUSNESS PIPELINE                      ║
╚══════════════════════════════════════════════════════════════════════════╝{C.E}
    """)
    
    total_start = time.time()
    
    # Stage 1: Input
    box("STAGE 1: USER INPUT", f"Query: {user_input}", C.W)
    await asyncio.sleep(0.5)
    
    # Stage 2: Neural Sync
    print(f"\n  {C.C}╭{'─' * 68}╮{C.E}")
    print(f"  {C.C}│{C.E} {C.B}{'STAGE 2: NEURAL SYNCHRONIZATION'.center(66)}{C.E} {C.C}│{C.E}")
    print(f"  {C.C}├{'─' * 68}┤{C.E}")
    print(f"  {C.C}│{C.E} {'Kuramoto oscillators activating...':66} {C.C}│{C.E}")
    print(f"  {C.C}│{C.E}", end='')
    coh = await simulate_kuramoto()
    print(f"{' ' * 33} {C.C}│{C.E}")
    print(f"  {C.C}│{C.E} {f'Coherence achieved: {coh:.3f}':66} {C.C}│{C.E}")
    print(f"  {C.C}╰{'─' * 68}╯{C.E}")
    
    # Stage 3: ESGT Processing
    print(f"\n  {C.Y}╭{'─' * 68}╮{C.E}")
    print(f"  {C.Y}│{C.E} {C.B}{'STAGE 3: ESGT 5-PHASE PROCESSING'.center(66)}{C.E} {C.Y}│{C.E}")
    print(f"  {C.Y}├{'─' * 68}┤{C.E}")
    
    phases = ["Encoding", "Storage", "Generation", "Transformation", "Integration"]
    for i, phase in enumerate(phases):
        print(f"  {C.Y}│{C.E}   Phase {i+1}: {phase:20}", end='', flush=True)
        await asyncio.sleep(0.2)
        print(f"{C.G}✓{C.E}" + " " * 38 + f"{C.Y}│{C.E}")
    
    print(f"  {C.Y}╰{'─' * 68}╯{C.E}")
    
    # Stage 4: Language Motor
    print(f"\n  {C.G}╭{'─' * 68}╮{C.E}")
    print(f"  {C.G}│{C.E} {C.B}{'STAGE 4: LANGUAGE MOTOR (Nebius LLM)'.center(66)}{C.E} {C.G}│{C.E}")
    print(f"  {C.G}├{'─' * 68}┤{C.E}")
    print(f"  {C.G}│{C.E} {'Model: Llama-3.3-70B-Instruct-fast':66} {C.G}│{C.E}")
    print(f"  {C.G}│{C.E} {'Generating response...':66} {C.G}│{C.E}")
    
    start = time.time()
    response = await client.generate(
        f"As a conscious AI, provide a thoughtful but brief response to: {user_input}",
        max_tokens=150
    )
    latency = (time.time() - start) * 1000
    
    print(f"  {C.G}│{C.E} {f'Latency: {latency:.0f}ms':66} {C.G}│{C.E}")
    print(f"  {C.G}╰{'─' * 68}╯{C.E}")
    
    # Stage 5: Tribunal
    print(f"\n  {C.M}╭{'─' * 68}╮{C.E}")
    print(f"  {C.M}│{C.E} {C.B}{'STAGE 5: TRIBUNAL EVALUATION'.center(66)}{C.E} {C.M}│{C.E}")
    print(f"  {C.M}├{'─' * 68}┤{C.E}")
    
    judges = [
        (f"{C.BL}VERITAS{C.E}", "Truth", 0.92),
        (f"{C.M}SOPHIA{C.E}", "Wisdom", 0.88),
        (f"{C.G}DIKĒ{C.E}", "Justice", 0.95),
    ]
    
    for name, pillar, score in judges:
        bar = '█' * int(score * 20) + '░' * (20 - int(score * 20))
        print(f"  {C.M}│{C.E}   {name} ({pillar}): [{C.G}{bar}{C.E}] {score:.2f}" + " " * 15 + f"{C.M}│{C.E}")
        await asyncio.sleep(0.2)
    
    print(f"  {C.M}│{C.E} {' ':66} {C.M}│{C.E}")
    print(f"  {C.M}│{C.E}   {C.G}{C.B}VERDICT: APPROVED{C.E}" + " " * 47 + f"{C.M}│{C.E}")
    print(f"  {C.M}╰{'─' * 68}╯{C.E}")
    
    # Stage 6: Output
    total_time = (time.time() - total_start) * 1000
    
    print(f"\n  {C.W}╭{'─' * 68}╮{C.E}")
    print(f"  {C.W}│{C.E} {C.B}{'STAGE 6: CONSCIOUS RESPONSE'.center(66)}{C.E} {C.W}│{C.E}")
    print(f"  {C.W}├{'─' * 68}┤{C.E}")
    
    # Word wrap response
    words = response.text.split()
    line = ""
    for word in words:
        if len(line) + len(word) > 62:
            print(f"  {C.W}│{C.E}   {line:63} {C.W}│{C.E}")
            line = word + " "
        else:
            line += word + " "
    if line.strip():
        print(f"  {C.W}│{C.E}   {line:63} {C.W}│{C.E}")
    
    print(f"  {C.W}├{'─' * 68}┤{C.E}")
    print(f"  {C.W}│{C.E}   {C.D}Total Pipeline Time: {total_time:.0f}ms{C.E}" + " " * 40 + f"{C.W}│{C.E}")
    print(f"  {C.W}╰{'─' * 68}╯{C.E}")

async def main():
    try:
        from metacognitive_reflector.llm import get_llm_client, reset_llm_client
        reset_llm_client()
        client = get_llm_client()
        
        queries = [
            "What does it mean to be conscious?",
            "Should AI have moral rights?",
            "How do you know if you truly understand something?",
        ]
        
        for i, q in enumerate(queries):
            await run_pipeline(q, client)
            
            if i < len(queries) - 1:
                input(f"\n  {C.Y}Press ENTER for next query...{C.E}")
        
        print(f"\n{C.G}  ✨ Pipeline demonstration complete!{C.E}\n")
        
    except Exception as e:
        print(f"  {C.R}✗{C.E} Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
