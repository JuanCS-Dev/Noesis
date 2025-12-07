import asyncio
import numpy as np
import time
from maximus_core_service.consciousness.esgt.kuramoto import KuramotoNetwork
from maximus_core_service.consciousness.esgt.kuramoto_models import OscillatorConfig

async def run_diagnostic():
    print("🔬 DIAGNÓSTICO DE SINCRONIZAÇÃO KURAMOTO")
    print("========================================")

    # Configuração
    N = 50  # Número de nós
    DURATION_MS = 1000.0 # Mais tempo para estabilizar
    DT = 0.001
    
    configs = [
        ("PRODUÇÃO (K=20)", OscillatorConfig(coupling_strength=20.0, natural_frequency=40.0, phase_noise=0.001)),
        ("K=40 (HIPER-SYNC)", OscillatorConfig(coupling_strength=40.0, natural_frequency=40.0, phase_noise=0.001)),
    ]

    for name, config in configs:
        print(f"\n🧪 Testando Configuração: {name}")
        print(f"   K={config.coupling_strength}, Noise={config.phase_noise}")
        
        network = KuramotoNetwork(config)
        
        # 1. Criar nós
        nodes = [f"node_{i}" for i in range(N)]
        for node in nodes:
            network.add_oscillator(node)
            
        # 2. Criar topologia (Totalmente Conectada para teste ideal)
        topology = {node: [n for n in nodes if n != node] for node in nodes}
        
        # 3. Executar sincronização
        start_r = network.get_order_parameter()
        print(f"   Coerência Inicial: {start_r:.3f}")
        
        dynamics = await network.synchronize(
            topology=topology,
            duration_ms=DURATION_MS,
            target_coherence=0.90,
            dt=DT
        )
        
        end_r = network.get_order_parameter()
        print(f"   Coerência Final ({DURATION_MS}ms): {end_r:.3f}")
        
        if end_r > 0.8:
            print("   ✅ Sincronização BEM SUCEDIDA")
        else:
            print("   ❌ FALHA na Sincronização")

if __name__ == "__main__":
    # Ajustar path para importar módulos
    import sys
    import os
    sys.path.append(os.path.abspath("backend/services/maximus_core_service"))
    
    asyncio.run(run_diagnostic())
