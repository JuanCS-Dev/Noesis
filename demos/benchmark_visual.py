#!/usr/bin/env python3
"""
NOESIS VISUAL BENCHMARK
=======================
A visually impressive benchmark that demonstrates LLM performance.
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'services', 'metacognitive_reflector', 'src'))

# Colors
class C:
    G = '\033[92m'
    Y = '\033[93m'
    R = '\033[91m'
    C = '\033[96m'
    W = '\033[97m'
    B = '\033[1m'
    D = '\033[2m'
    E = '\033[0m'

def bar(val, mx=100, w=40):
    filled = int((val/mx) * w)
    return f"{'█' * filled}{'░' * (w-filled)}"

async def benchmark():
    print(f"\n{C.C}{'═' * 70}{C.E}")
    print(f"{C.B}{C.W}  🚀 NOESIS LLM PERFORMANCE BENCHMARK{C.E}")
    print(f"{C.C}{'═' * 70}{C.E}\n")
    
    try:
        from metacognitive_reflector.llm import get_llm_client, reset_llm_client
        reset_llm_client()
        client = get_llm_client()
        
        print(f"  {C.G}✓{C.E} Connected to Nebius Token Factory")
        print(f"  {C.D}Model: {client.config.nebius.model}{C.E}\n")
        
        tests = [
            ("Simple Response", "Say 'OK'", 10),
            ("Short Answer", "What is 2+2?", 20),
            ("Explanation", "Explain consciousness in one sentence", 100),
            ("Reasoning", "Is it ethical to lie to protect someone?", 200),
        ]
        
        results = []
        
        for name, prompt, max_tok in tests:
            print(f"  {C.Y}▶{C.E} {name}", end="", flush=True)
            
            start = time.time()
            resp = await client.generate(prompt, max_tokens=max_tok)
            latency = (time.time() - start) * 1000
            
            results.append((name, latency, resp.total_tokens))
            
            # Visual bar
            speed_score = min(100, (3000 / latency) * 50)
            color = C.G if latency < 1500 else C.Y if latency < 3000 else C.R
            print(f"\r  {color}●{C.E} {name:20} {latency:6.0f}ms [{bar(speed_score)}]")
        
        # Summary
        avg = sum(r[1] for r in results) / len(results)
        print(f"\n{C.C}{'─' * 70}{C.E}")
        print(f"  Average Latency: {C.G if avg < 2000 else C.Y}{avg:.0f}ms{C.E}")
        print(f"  Total Tokens: {sum(r[2] for r in results)}")
        print(f"{C.C}{'─' * 70}{C.E}\n")
        
    except Exception as e:
        print(f"  {C.R}✗{C.E} Error: {e}")

if __name__ == "__main__":
    asyncio.run(benchmark())
