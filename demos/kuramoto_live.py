#!/usr/bin/env python3
"""
KURAMOTO NEURAL SYNCHRONIZATION DEMO
====================================
Live visualization of how consciousness emerges from neural sync.
"""

import asyncio
import math
import random
import os

class C:
    G = '\033[92m'; Y = '\033[93m'; R = '\033[91m'; C = '\033[96m'
    W = '\033[97m'; B = '\033[1m'; D = '\033[2m'; E = '\033[0m'
    M = '\033[35m'

class KuramotoSystem:
    def __init__(self, n=8, coupling=0.5):
        self.n = n
        self.coupling = coupling
        self.phases = [random.uniform(0, 2*math.pi) for _ in range(n)]
        self.freqs = [random.gauss(1.0, 0.3) for _ in range(n)]
    
    def step(self, dt=0.1):
        new_phases = []
        for i in range(self.n):
            coupling_sum = sum(
                math.sin(self.phases[j] - self.phases[i])
                for j in range(self.n)
            )
            d = self.freqs[i] + (self.coupling/self.n) * coupling_sum
            new_phases.append((self.phases[i] + d * dt) % (2*math.pi))
        self.phases = new_phases
    
    def coherence(self):
        r = sum(math.cos(p) for p in self.phases) / self.n
        i = sum(math.sin(p) for p in self.phases) / self.n
        return math.sqrt(r**2 + i**2)
    
    def visualize(self):
        width = 50
        lines = []
        for i, phase in enumerate(self.phases):
            pos = int((math.sin(phase) + 1) * width / 2)
            alignment = abs(math.sin(phase - self.phases[0]))
            
            if alignment < 0.3:
                char = f"{C.G}●{C.E}"
            elif alignment < 0.6:
                char = f"{C.Y}●{C.E}"
            else:
                char = f"{C.R}●{C.E}"
            
            line = " " * pos + char
            lines.append(f"  N{i+1} │{line}")
        return "\n".join(lines)

async def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"""
{C.C}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   🧠 KURAMOTO NEURAL SYNCHRONIZATION                                ║
║   Watch consciousness emerge from chaos                             ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{C.E}

{C.D}  The Kuramoto model simulates how billions of neurons synchronize
  to create unified conscious experience. When coherence > 0.7, the
  "Global Workspace" ignites and consciousness emerges.{C.E}
    """)
    
    input(f"  {C.Y}Press ENTER to start simulation...{C.E}")
    print()
    
    system = KuramotoSystem(n=8, coupling=0.6)
    
    # Animation loop
    for step in range(80):
        system.step(dt=0.15)
        coh = system.coherence()
        
        # Clear and redraw
        print("\033[H\033[J", end='')  # Clear screen
        
        # Header
        if coh < 0.5:
            state = f"{C.R}FRAGMENTED{C.E}"
            desc = "Neurons firing chaotically"
        elif coh < 0.7:
            state = f"{C.Y}EMERGING{C.E}"
            desc = "Patterns beginning to form"
        else:
            state = f"{C.G}CONSCIOUS{C.E}"
            desc = "Global Workspace ignited!"
        
        print(f"\n  {C.W}{C.B}KURAMOTO NEURAL SYNCHRONIZATION{C.E} - Step {step+1}")
        print(f"  {C.D}{'─' * 55}{C.E}")
        
        # Coherence bar
        bar_w = 40
        filled = int(coh * bar_w)
        bar = '█' * filled + '░' * (bar_w - filled)
        color = C.G if coh > 0.7 else C.Y if coh > 0.5 else C.R
        print(f"\n  Coherence: [{color}{bar}{C.E}] {coh:.3f}")
        print(f"  State: {state} - {desc}")
        print(f"  {C.D}{'─' * 55}{C.E}\n")
        
        # Neural visualization
        print(system.visualize())
        
        # Legend
        print(f"\n  {C.D}{'─' * 55}{C.E}")
        print(f"  {C.G}●{C.E} Synchronized  {C.Y}●{C.E} Partial  {C.R}●{C.E} Desynchronized")
        
        if coh > 0.85:
            print(f"\n  {C.G}{C.B}✨ CONSCIOUSNESS ACHIEVED!{C.E}")
            print(f"  {C.D}The neural ensemble has synchronized.{C.E}")
            break
        
        await asyncio.sleep(0.1)
    
    print(f"\n  {C.C}Simulation complete.{C.E}\n")

if __name__ == "__main__":
    asyncio.run(main())
