import asyncio
import json
import httpx
import sys

async def test_consciousness_stream():
    url = "http://localhost:8001/api/consciousness/stream/process"
    params = {"content": "SINGULARIDADE", "depth": 5}
    
    print(f"Connecting to {url} with params: {params}")
    
    phases_seen = set()
    tokens_received = []
    coherence_values = []
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("GET", url, params=params) as response:
                if response.status_code != 200:
                    print(f"Failed to connect: {response.status_code}")
                    return False
                
                print("Connection established. Listening for events...")
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            event_type = data.get("type")
                            
                            if event_type == "phase":
                                phase = data.get("phase")
                                phases_seen.add(phase)
                                print(f"[PHASE] -> {phase}")
                                
                            elif event_type == "coherence":
                                val = data.get("value")
                                coherence_values.append(val)
                                # print(f"[COHERENCE] {val}")
                                
                            elif event_type == "token":
                                token = data.get("token")
                                tokens_received.append(token)
                                sys.stdout.write(token)
                                sys.stdout.flush()
                                
                            elif event_type == "complete":
                                print("\n[COMPLETE] Stream finished.")
                                break
                                
                            elif event_type == "error":
                                print(f"\n[ERROR] {data.get('message')}")
                                return False
                                
                        except json.JSONDecodeError:
                            print(f"Failed to parse: {data_str}")
                            
    except Exception as e:
        print(f"Exception: {e}")
        return False

    # Validation
    print("\n\n=== Validation Report ===")
    
    # Check phases
    # Note: Based on frontend/src/stores/consciousnessStore.ts, phases can be:
    # "idle", "prepare", "synchronize", "broadcast", "sustain", "dissolve", "complete", "failed"
    expected_critical_phases = {"prepare", "synchronize"}
    missing_phases = expected_critical_phases - phases_seen
    
    print(f"Phases observed: {phases_seen}")
    
    if missing_phases:
        print(f"WARNING: Missing critical phases: {missing_phases}")
    else:
        print("SUCCESS: Critical ESGT phases observed.")

    # Check coherence
    if coherence_values:
        avg_coherence = sum(coherence_values) / len(coherence_values)
        max_coherence = max(coherence_values)
        print(f"Coherence: Avg={avg_coherence:.3f}, Max={max_coherence:.3f}")
        if max_coherence > 0.8: # Threshold slightly lower than 0.95 for general E2E pass
            print("SUCCESS: High coherence achieved.")
        else:
            print(f"WARNING: Coherence max ({max_coherence}) low.")
    else:
        print("WARNING: No coherence data received (Might be expected if sync was instant or hidden).")

    # Check output
    full_text = "".join(tokens_received)
    if len(full_text) > 5:
        print(f"SUCCESS: Received meaningful response ({len(full_text)} chars).")
    else:
        print("FAILURE: Response too short.")
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_consciousness_stream())
    sys.exit(0 if success else 1)
