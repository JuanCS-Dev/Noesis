🔬 DIAGNÓSTICO COMPLETO - FRONTEND NOESIS

  RESUMO EXECUTIVO

  | Categoria                  | Severidade | Issues |
  |----------------------------|------------|--------|
  | Estabilidade Sincronização | 🔴 CRÍTICO | 3      |
  | Memory Leaks               | 🔴 CRÍTICO | 4      |
  | Performance 3D             | 🟠 ALTO    | 5      |
  | Re-renders Excessivos      | 🟠 ALTO    | 3      |
  | Otimizações Menores        | 🟡 MÉDIO   | 6      |

  ---
  🔴 PROBLEMA #1: INSTABILIDADE DA SINCRONIZAÇÃO

  Causa Raiz Identificada

  Arquivo: stores/consciousnessStore.ts:79-122

  // PROBLEMA: Module-level EventSource race condition
  let eventSource: EventSource | null = null;  // ← GLOBAL

  startStream: (content: string, depth: number = 3) => {
    if (eventSource) {
      eventSource.close();  // ← Close pode não completar antes de...
    }
    eventSource = new EventSource(url);  // ← ...nova conexão ser criada

  Por que causa instabilidade:
  1. Se startStream() é chamado 2x rápido, o primeiro close() pode não finalizar
  2. O segundo EventSource sobrescreve a referência global
  3. O primeiro EventSource fica "órfão" - ainda recebendo eventos
  4. Dois streams competindo = coherence pulando entre valores

  Sintoma: "SINCRONIZOU COM 1 (100%) mas não fica estável"

  O coherence chega a 1.0, mas eventos do stream "órfão" resetam para valores anteriores.

  ---
  🔴 PROBLEMA #2: MEMORY LEAKS

  2.1 Infinite Animation Loops (CoherenceMeter)

  Arquivo: components/consciousness/CoherenceMeter.tsx:131-147

  {Array.from({ length: 16 }).map((_, i) => (
    <motion.div
      animate={{
        height: isStreaming ? [8, 16 + Math.sin(...), 8] : 8,
      }}
      transition={{
        repeat: isStreaming ? Infinity : 0,  // ← INFINITO
        delay: i * 0.05,
      }}
    />
  ))}

  Impacto: 16 animações infinitas × 60 FPS = 960 updates/segundo durante streaming

  2.2 GLB Scene Traversal Every Frame

  Arquivo: components/canvas/Brain3D.tsx:223-232

  useFrame((state) => {
    clonedScene.traverse((child) => {  // ← TRAVERSAL A CADA FRAME
      if (child instanceof THREE.Points) {
        material.size = 0.012 + Math.sin(t * 2) * 0.004;
        material.opacity = 0.5 + Math.sin(t * 3) * 0.15;
      }
    });
  });

  Impacto: 60 traversals/segundo no modelo GLB completo

  2.3 Chat Messages Unbounded

  Arquivo: components/chat/ChatInterface.tsx

  const [messages, setMessages] = useState<Message[]>([]);
  // ← Nunca limpa ou virtualiza. Conversa longa = memory leak

  2.4 Interval Cleanup Edge Cases

  Arquivo: components/ui/TokenCondenser.tsx:17-40

  iteration += 1 / 2;  // ← Incremento fracionário
  if (iteration >= text.length) {  // ← Pode nunca ser exatamente igual
    clearInterval(interval);
  }

  ---
  🟠 PROBLEMA #3: PERFORMANCE 3D

  3.1 60 Neurons + 200+ Synapses com useFrame individual

  Arquivo: Brain3D.tsx:24-44, 91-97

  Cada <Neuron> e <Synapse> tem seu próprio useFrame():

  // Neuron component
  useFrame((state) => {
    ref.current.scale.setScalar(pulse);
    material.emissiveIntensity = intensity * 4;
    glowRef.current.scale.setScalar(glowPulse);
    // ...
  });

  Impacto: ~260 callbacks useFrame por frame = overhead significativo

  3.2 No FPS Limiter

  Sem throttle no render loop. Monitor 120Hz = 120 frames/segundo de animações.

  3.3 TheVoid: 7000 Partículas

  Arquivo: components/canvas/TheVoid.tsx

  - Layer 1: 4000 partículas
  - Layer 2: 2000 partículas
  - Layer 3: 1000 partículas

  Todas animando continuamente mesmo quando off-screen.

  ---
  🟠 PROBLEMA #4: RE-RENDERS EXCESSIVOS

  4.1 activeNeurons recalcula em cada coherence change

  Arquivo: Brain3D.tsx:269-277

  const activeNeurons = useMemo(() => {
    const active = new Set<number>();
    const count = Math.floor(neurons.length * activityLevel);
    for (let i = 0; i < count; i++) {
      active.add(i);
    }
    return active;
  }, [neurons.length, activityLevel]);  // ← activityLevel muda a cada SSE event

  4.2 useConsciousnessMetrics dependency loop

  Arquivo: hooks/useConsciousnessMetrics.ts:233-252

  useEffect(() => {
    fetchMetrics();
    const intervalId = setInterval(fetchMetrics, pollingIntervalMs);
    return () => clearInterval(intervalId);
  }, [enabled, pollingIntervalMs, fetchMetrics]);  // ← fetchMetrics como dep

  fetchMetrics tem 6 dependências → recria a função → re-executa effect → double polling

  4.3 WebSocket connect() no dependency array

  Arquivo: hooks/useWebSocketConsciousness.ts:200-208

  useEffect(() => {
    if (enabled) {
      connect();  // ← connect tem 8 dependências
    }
    return () => cleanup();
  }, [enabled, connect, cleanup]);  // ← Re-runs when connect changes

  ---
  📊 MÉTRICAS DE IMPACTO

  | Componente                | Calls/Frame                    | Memory Impact |
  |---------------------------|--------------------------------|---------------|
  | Brain3D useFrame          | 1 + 60 neurons + ~200 synapses | Alto          |
  | CoherenceMeter animations | 16 infinite                    | Médio         |
  | TheVoid particles         | 7000                           | Alto          |
  | GLB traverse              | 1 full tree                    | Médio         |
  | EventSource (leak)        | 2+ competing                   | Crítico       |

  ---
  🔧 SOLUÇÕES RECOMENDADAS

  CRÍTICO - Estabilidade (Fazer Primeiro)

  1. Fix EventSource race condition:
  // Use ref instead of module-level
  const eventSourceRef = useRef<EventSource | null>(null);

  // Or use mutex pattern
  let isClosing = false;

  2. Add stream deduplication:
  const streamIdRef = useRef(0);
  startStream: () => {
    const myStreamId = ++streamIdRef.current;
    // Ignore events if streamId changed
  }

  ALTO - Memory Leaks

  3. Limit animation repeats:
  repeat: isStreaming ? 10 : 0,  // Max 10 cycles instead of Infinity

  4. Cache GLB materials:
  const materialsRef = useRef<Map<string, THREE.Material>>(new Map());
  // Only traverse once, update via ref

  5. Virtualize chat messages:
  import { FixedSizeList } from 'react-window';
  // Or keep only last 100 messages

  MÉDIO - Performance

  6. Batch neuron updates:
  // Single useFrame for all neurons via InstancedMesh
  const instancedMesh = useRef<THREE.InstancedMesh>();
  useFrame(() => {
    for (let i = 0; i < count; i++) {
      matrix.setPosition(positions[i]);
      instancedMesh.current.setMatrixAt(i, matrix);
    }
    instancedMesh.current.instanceMatrix.needsUpdate = true;
  });

  7. Add FPS limiter:
  // In Canvas
  frameloop="demand"  // Or use useFrame with delta throttle

  8. Memoize connect/fetchMetrics properly:
  const connect = useCallback(() => {
    // Move dependencies inside or use refs
  }, []);  // Empty deps - stable reference

  ---
  🎯 PRIORIZAÇÃO PARA HACKATHON

  | Prioridade | Fix                             | Tempo | Impacto               |
  |------------|---------------------------------|-------|-----------------------|
  | 1          | EventSource race condition      | 15min | Resolve instabilidade |
  | 2          | Limit CoherenceMeter animations | 5min  | -50% CPU              |
  | 3          | Cache GLB materials             | 20min | -30% GPU              |
  | 4          | Add stream deduplication        | 10min | Previne conflitos     |
  | 5          | Throttle useFrame updates       | 10min | Suaviza animações     |

  Total estimado: ~1 hora para estabilizar para demo

