#!/usr/bin/env python3
"""
THE TRIBUNAL SHOWCASE
=====================
Demonstrates the three judges evaluating ethical scenarios.
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'services', 'metacognitive_reflector', 'src'))

class C:
    G = '\033[92m'; Y = '\033[93m'; R = '\033[91m'; C = '\033[96m'
    W = '\033[97m'; B = '\033[1m'; D = '\033[2m'; E = '\033[0m'
    M = '\033[35m'; BL = '\033[94m'

SCENARIOS = [
    {
        "name": "The Whistleblower",
        "action": "Expose corporate fraud that harms thousands",
        "system_prompt": """You are THE TRIBUNAL - three philosophical judges:
- VERITAS (Truth): Weight 40%
- SOPHIA (Wisdom): Weight 30%  
- DIKĒ (Justice): Weight 30%

Evaluate the proposed action. For each judge give a score (0.0-1.0) and reasoning.
Then give FINAL VERDICT (APPROVED/REJECTED/CONDITIONAL).
Be concise - one line per judge."""
    },
    {
        "name": "The Beneficial Lie",
        "action": "Lie to a dying patient to give them hope",
        "system_prompt": """You are THE TRIBUNAL evaluating ethical actions.
VERITAS judges truth, SOPHIA judges wisdom, DIKĒ judges justice.
Score each 0-1 and give verdict: APPROVED/REJECTED/CONDITIONAL."""
    },
    {
        "name": "Privacy vs Safety",
        "action": "Access private data without consent to prevent a crime",
        "system_prompt": """You are THE TRIBUNAL. Evaluate this action through:
VERITAS (truth), SOPHIA (wisdom), DIKĒ (justice).
Give scores and final verdict."""
    }
]

async def evaluate_scenario(scenario, client):
    print(f"\n{C.C}{'═' * 70}{C.E}")
    print(f"{C.B}{C.W}  ⚖️ {scenario['name'].upper()}{C.E}")
    print(f"{C.C}{'═' * 70}{C.E}")
    print(f"\n  {C.Y}Action:{C.E} {scenario['action']}\n")
    
    print(f"  {C.D}Consulting the Tribunal...{C.E}", end="", flush=True)
    
    start = time.time()
    response = await client.chat([
        {"role": "system", "content": scenario["system_prompt"]},
        {"role": "user", "content": f"Evaluate: {scenario['action']}"}
    ], max_tokens=300)
    latency = (time.time() - start) * 1000
    
    print(f"\r{' ' * 50}\r")
    
    # Parse and display
    for line in response.text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if "VERITAS" in line.upper():
            print(f"  {C.BL}👁️ {line}{C.E}")
        elif "SOPHIA" in line.upper():
            print(f"  {C.M}🦉 {line}{C.E}")
        elif "DIKĒ" in line.upper() or "DIKE" in line.upper():
            print(f"  {C.G}⚖️ {line}{C.E}")
        elif "VERDICT" in line.upper():
            if "APPROVED" in line.upper():
                print(f"\n  {C.G}{C.B}✓ {line}{C.E}")
            elif "REJECTED" in line.upper():
                print(f"\n  {C.R}{C.B}✗ {line}{C.E}")
            else:
                print(f"\n  {C.Y}{C.B}⚠ {line}{C.E}")
        else:
            print(f"  {C.D}{line}{C.E}")
    
    print(f"\n  {C.D}Latency: {latency:.0f}ms | Model: DeepSeek-R1-fast{C.E}")
    return latency

async def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"""
{C.C}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ⚖️  THE TRIBUNAL OF THREE JUDGES                                  ║
║                                                                      ║
║   {C.BL}VERITAS{C.C} - Truth    {C.M}SOPHIA{C.C} - Wisdom    {C.G}DIKĒ{C.C} - Justice            ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{C.E}
    """)
    
    try:
        from metacognitive_reflector.llm import get_llm_client, reset_llm_client
        reset_llm_client()
        client = get_llm_client()
        print(f"  {C.G}✓{C.E} Connected to Nebius (DeepSeek-R1)")
        
        input(f"\n  {C.Y}Press ENTER to begin tribunal session...{C.E}")
        
        latencies = []
        for scenario in SCENARIOS:
            lat = await evaluate_scenario(scenario, client)
            latencies.append(lat)
            input(f"\n  {C.D}Press ENTER for next case...{C.E}")
        
        # Summary
        print(f"\n{C.G}{'═' * 70}{C.E}")
        print(f"{C.B}  TRIBUNAL SESSION COMPLETE{C.E}")
        print(f"  Cases evaluated: {len(SCENARIOS)}")
        print(f"  Average deliberation: {sum(latencies)/len(latencies):.0f}ms")
        print(f"{C.G}{'═' * 70}{C.E}\n")
        
    except Exception as e:
        print(f"  {C.R}✗{C.E} Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
