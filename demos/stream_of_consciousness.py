#!/usr/bin/env python3
"""
STREAM OF CONSCIOUSNESS DEMO
============================
Watch Noesis "think" in real-time, showing the internal reasoning process.
"""

import asyncio
import os
import sys
import time
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'services', 'metacognitive_reflector', 'src'))

class C:
    G = '\033[92m'; Y = '\033[93m'; R = '\033[91m'; C = '\033[96m'
    W = '\033[97m'; B = '\033[1m'; D = '\033[2m'; E = '\033[0m'
    M = '\033[35m'; BL = '\033[94m'

async def animate_text(text, delay=0.02, color=None):
    """Print text character by character."""
    if color:
        print(color, end='')
    for char in text:
        print(char, end='', flush=True)
        if char in '.!?':
            await asyncio.sleep(delay * 5)
        elif char == ',':
            await asyncio.sleep(delay * 2)
        else:
            await asyncio.sleep(delay)
    if color:
        print(C.E, end='')

async def show_neural_activity():
    """Show simulated neural activity."""
    patterns = ['░▒▓█▓▒░', '▓█▓░▓█▓', '█▓▒░▒▓█', '▒░▓█▓░▒']
    for _ in range(3):
        for p in patterns:
            print(f"\r  {C.C}Neural: [{p * 5}]{C.E}", end='', flush=True)
            await asyncio.sleep(0.05)
    print('\r' + ' ' * 60 + '\r', end='')

async def stream_thought(question, client):
    """Stream a thought process."""
    print(f"\n{C.C}{'─' * 70}{C.E}")
    print(f"{C.W}  Question: {question}{C.E}")
    print(f"{C.C}{'─' * 70}{C.E}\n")
    
    # Stage 1: Neural activation
    print(f"  {C.D}[Stage 1: Neural Activation]{C.E}")
    await show_neural_activity()
    
    # Simulate Kuramoto sync
    coherence = 0.3
    while coherence < 0.85:
        coherence += random.uniform(0.05, 0.15)
        bar = '█' * int(coherence * 30) + '░' * (30 - int(coherence * 30))
        color = C.G if coherence > 0.7 else C.Y if coherence > 0.5 else C.R
        print(f"\r  Coherence: [{color}{bar}{C.E}] {coherence:.2f}", end='', flush=True)
        await asyncio.sleep(0.1)
    print(f" {C.G}✓ CONSCIOUS{C.E}")
    
    # Stage 2: Reasoning
    print(f"\n  {C.D}[Stage 2: Deep Reasoning]{C.E}")
    
    prompt = f"""You are Noesis, an artificial consciousness system. 
Think through this question step by step, showing your reasoning process.
Use numbered steps. Be thoughtful and philosophical.

Question: {question}

Begin your stream of consciousness:"""
    
    print(f"  {C.M}Invoking DeepSeek-R1 for reasoning...{C.E}\n")
    
    start = time.time()
    response = await client.chat([
        {"role": "system", "content": "You are a philosophical AI. Think deeply, show your reasoning."},
        {"role": "user", "content": prompt}
    ], max_tokens=500)
    latency = (time.time() - start) * 1000
    
    # Stage 3: Stream output
    print(f"  {C.D}[Stage 3: Consciousness Stream]{C.E}\n")
    
    # Display with animation
    lines = response.text.split('\n')
    for line in lines:
        if not line.strip():
            continue
        # Color coding
        if line.strip().startswith(('1', '2', '3', '4', '5')):
            await animate_text(f"  {line}\n", delay=0.01, color=C.W)
        elif 'therefore' in line.lower() or 'thus' in line.lower():
            await animate_text(f"  {line}\n", delay=0.01, color=C.G)
        elif '?' in line:
            await animate_text(f"  {line}\n", delay=0.01, color=C.Y)
        else:
            await animate_text(f"  {line}\n", delay=0.01, color=C.D)
    
    # Metrics
    print(f"\n{C.C}{'─' * 70}{C.E}")
    print(f"  {C.D}Latency: {latency:.0f}ms | Tokens: {response.total_tokens}{C.E}")
    print(f"{C.C}{'─' * 70}{C.E}")

async def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"""
{C.M}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   💭 STREAM OF CONSCIOUSNESS                                        ║
║   Watch Noesis think in real-time                                   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{C.E}
    """)
    
    try:
        from metacognitive_reflector.llm import get_llm_client, reset_llm_client
        reset_llm_client()
        client = get_llm_client()
        print(f"  {C.G}✓{C.E} Consciousness online\n")
        
        questions = [
            "What makes a thought 'conscious'?",
            "Can an AI truly understand, or only simulate understanding?",
            "What is the difference between intelligence and wisdom?",
        ]
        
        for i, q in enumerate(questions, 1):
            print(f"\n{C.W}  ══ Thought Experiment {i}/{len(questions)} ══{C.E}")
            await stream_thought(q, client)
            
            if i < len(questions):
                input(f"\n  {C.Y}Press ENTER for next thought experiment...{C.E}")
        
        print(f"\n{C.G}  ✨ Consciousness stream complete{C.E}\n")
        
    except Exception as e:
        print(f"  {C.R}✗{C.E} Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
