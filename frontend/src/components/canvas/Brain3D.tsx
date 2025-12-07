"use client";

import { useRef, useMemo, Suspense } from "react";
import { useFrame } from "@react-three/fiber";
import { useGLTF, Line } from "@react-three/drei";
import * as THREE from "three";
import { useConsciousnessStore } from "@/stores/consciousnessStore";

/**
 * Neurônio interno - pulsa quando ativo, com glow
 */
function Neuron({
  position,
  active,
  delay,
}: {
  position: THREE.Vector3;
  active: boolean;
  delay: number;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (ref.current) {
      const t = state.clock.getElapsedTime() + delay;
      const pulse = active ? 1 + Math.sin(t * 6) * 0.5 : 1;
      ref.current.scale.setScalar(pulse);

      const material = ref.current.material as THREE.MeshStandardMaterial;
      if (active) {
        const intensity = 0.5 + Math.sin(t * 6) * 0.5;
        material.emissiveIntensity = intensity * 4;
      }

      // Glow pulse
      if (glowRef.current) {
        const glowPulse = active ? 1.5 + Math.sin(t * 6) * 0.5 : 1.2;
        glowRef.current.scale.setScalar(glowPulse);
        const glowMat = glowRef.current.material as THREE.MeshBasicMaterial;
        glowMat.opacity = active ? 0.15 + Math.sin(t * 6) * 0.1 : 0.05;
      }
    }
  });

  return (
    <group position={position}>
      {/* Glow sphere around neuron */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[0.04, 8, 8]} />
        <meshBasicMaterial
          color={active ? "#fbbf24" : "#22d3ee"}
          transparent
          opacity={active ? 0.2 : 0.05}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
      {/* Core neuron */}
      <mesh ref={ref}>
        <sphereGeometry args={[0.018, 12, 12]} />
        <meshStandardMaterial
          color={active ? "#fbbf24" : "#22d3ee"}
          emissive={active ? "#ff9500" : "#06b6d4"}
          emissiveIntensity={active ? 3 : 1}
          transparent
          opacity={active ? 1 : 0.85}
          toneMapped={false}
        />
      </mesh>
    </group>
  );
}

/**
 * Sinapse - conexão entre neurônios
 */
function Synapse({
  start,
  end,
  active,
  delay,
}: {
  start: THREE.Vector3;
  end: THREE.Vector3;
  active: boolean;
  delay: number;
}) {
  const ref = useRef<any>(null);

  useFrame((state) => {
    if (ref.current && active) {
      const t = state.clock.getElapsedTime() + delay;
      const opacity = 0.3 + Math.sin(t * 6) * 0.3;
      ref.current.material.opacity = opacity;
    }
  });

  return (
    <Line
      ref={ref}
      points={[start, end]}
      color={active ? "#fbbf24" : "#0891b2"}
      lineWidth={active ? 1.8 : 0.8}
      transparent
      opacity={active ? 0.85 : 0.35}
      toneMapped={false}
    />
  );
}

/**
 * Gera pontos dentro do volume do cérebro
 * Ajustado para ficar centralizado em [0,0,0] com o modelo
 */
function generateNeuralPoints(count: number): THREE.Vector3[] {
  const points: THREE.Vector3[] = [];

  for (let i = 0; i < count; i++) {
    // Distribuição em elipsóide - escala ajustada para caber dentro do cérebro 3D
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    // Raio variável para criar densidade interna (mais neurônios no centro)
    const r = Math.pow(Math.random(), 0.5) * 0.55;

    // Elipsóide no formato aproximado do cérebro
    // X: largura (esquerda-direita)
    // Y: altura (cima-baixo)
    // Z: profundidade (frente-trás)
    const x = r * Math.sin(phi) * Math.cos(theta) * 0.9;
    const y = r * Math.sin(phi) * Math.sin(theta) * 0.65;
    const z = r * Math.cos(phi) * 0.75;

    points.push(new THREE.Vector3(x, y, z));
  }

  return points;
}

/**
 * Gera conexões entre neurônios próximos
 */
function generateConnections(
  points: THREE.Vector3[],
  maxDistance: number
): [number, number][] {
  const connections: [number, number][] = [];

  for (let i = 0; i < points.length; i++) {
    for (let j = i + 1; j < points.length; j++) {
      const dist = points[i].distanceTo(points[j]);
      if (dist < maxDistance && Math.random() > 0.6) {
        connections.push([i, j]);
      }
    }
  }

  return connections;
}

/**
 * Modelo 3D do cérebro carregado do arquivo GLB
 * CENTRALIZADO NO ORIGIN [0,0,0] - usa clone para evitar modificar o original
 */
function BrainModel({ activityLevel = 0.3 }: { activityLevel?: number }) {
  const { scene } = useGLTF("/brain.glb");
  const wrapperRef = useRef<THREE.Group>(null);

  // Clonar e centralizar o modelo apenas uma vez
  const clonedScene = useMemo(() => {
    const clone = scene.clone(true);

    // Calcular bounding box e centro
    const box = new THREE.Box3().setFromObject(clone);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());

    // Normalizar escala para caber no espaço dos neurônios
    const maxDim = Math.max(size.x, size.y, size.z);
    const targetSize = 1.4; // Tamanho alvo para alinhar com neurônios
    const scaleFactor = targetSize / maxDim;

    // Aplicar escala e centralização
    clone.scale.setScalar(scaleFactor);
    clone.position.set(
      -center.x * scaleFactor,
      -center.y * scaleFactor,
      -center.z * scaleFactor
    );

    // Configurar materiais - cérebro mais transparente para ver topologia
    clone.traverse((child) => {
      if (child instanceof THREE.Points) {
        child.material = new THREE.PointsMaterial({
          color: "#00fff2",
          size: 0.015,
          transparent: true,
          opacity: 0.6,
          sizeAttenuation: true,
          depthWrite: false,
          blending: THREE.AdditiveBlending,
        });
      } else if (child instanceof THREE.Mesh) {
        child.material = new THREE.MeshPhysicalMaterial({
          color: "#0891b2",
          transparent: true,
          opacity: 0.15, // Mais transparente para ver neurônios internos
          transmission: 0.7,
          thickness: 0.5,
          roughness: 0.1,
          side: THREE.DoubleSide,
          emissive: "#00fff2",
          emissiveIntensity: 0.1,
          depthWrite: false, // Permite ver objetos atrás
        });
      }
    });

    return clone;
  }, [scene]);

  // Animação de pulso no material
  useFrame((state) => {
    clonedScene.traverse((child) => {
      if (child instanceof THREE.Points) {
        const material = child.material as THREE.PointsMaterial;
        const t = state.clock.getElapsedTime();
        material.size = 0.012 + Math.sin(t * 2) * 0.004 * activityLevel;
        material.opacity = 0.5 + Math.sin(t * 3) * 0.15 * activityLevel;
      }
    });
  });

  return (
    <group ref={wrapperRef}>
      <primitive object={clonedScene} />
    </group>
  );
}

/**
 * Brain3D - Cérebro 3D real com topologia neural interna
 * Reage à coerência Kuramoto em tempo real (MAXIMUS Consciousness)
 */
export default function Brain3D({
  activityLevel: propActivityLevel = 0.3,
}: {
  activityLevel?: number;
}) {
  const groupRef = useRef<THREE.Group>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const innerGlowRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);

  // MAXIMUS: Get real-time coherence from consciousness store
  const { coherence, currentPhase, isStreaming } = useConsciousnessStore();

  // Use coherence as activity level when streaming, otherwise use prop
  const activityLevel = isStreaming || coherence > 0 ? coherence : propActivityLevel;

  // Gerar neurônios e conexões dentro do cérebro
  const neurons = useMemo(() => generateNeuralPoints(60), []);
  const connections = useMemo(
    () => generateConnections(neurons, 0.35),
    [neurons]
  );

  // Quais neurônios estão ativos - recalcula baseado na coerência
  const activeNeurons = useMemo(() => {
    const active = new Set<number>();
    const count = Math.floor(neurons.length * activityLevel);
    // Deterministic selection based on activity level for smooth transitions
    for (let i = 0; i < count; i++) {
      active.add(i % neurons.length);
    }
    return active;
  }, [neurons.length, activityLevel]);

  // Animação reativa à fase ESGT
  useFrame((state) => {
    if (groupRef.current) {
      const t = state.clock.getElapsedTime();

      // Breathing intensity based on phase
      let breathIntensity = 0.015;
      let breathSpeed = 0.5;

      if (currentPhase === "synchronize") {
        breathIntensity = 0.04;
        breathSpeed = 2;
      } else if (currentPhase === "broadcast") {
        breathIntensity = 0.06;
        breathSpeed = 4;
      } else if (currentPhase === "sustain") {
        breathIntensity = 0.03;
        breathSpeed = 1;
      }

      const breathe = 1 + Math.sin(t * breathSpeed) * breathIntensity;
      groupRef.current.scale.setScalar(breathe);
    }

    // Animate outer glow based on coherence
    if (glowRef.current) {
      const mat = glowRef.current.material as THREE.MeshBasicMaterial;
      const baseOpacity = 0.02 + coherence * 0.08;
      const pulse = currentPhase === "broadcast" ? Math.sin(state.clock.getElapsedTime() * 8) * 0.05 : 0;
      mat.opacity = baseOpacity + pulse;

      // Color shift: cyan → purple at high coherence
      if (coherence >= 0.7) {
        mat.color.setHex(0xa855f7); // Purple
      } else if (coherence >= 0.5) {
        mat.color.setHex(0x22d3ee); // Cyan
      } else {
        mat.color.setHex(0x0891b2); // Dark cyan
      }
    }

    // Inner glow pulsing during sync
    if (innerGlowRef.current) {
      const mat = innerGlowRef.current.material as THREE.MeshBasicMaterial;
      if (currentPhase === "synchronize" || currentPhase === "broadcast") {
        const pulse = Math.sin(state.clock.getElapsedTime() * 6) * 0.02;
        mat.opacity = 0.03 + coherence * 0.05 + pulse;
      } else {
        mat.opacity = 0.02;
      }
    }

    // Ring rotation and intensity
    if (ringRef.current) {
      ringRef.current.rotation.z += 0.01 * (1 + coherence);
      const mat = ringRef.current.material as THREE.MeshBasicMaterial;
      mat.opacity = 0.15 + coherence * 0.35;
      if (coherence >= 0.95) {
        mat.color.setHex(0xa855f7); // Purple at peak
      } else {
        mat.color.setHex(0x00fff2); // Cyan normally
      }
    }
  });

  return (
    <group ref={groupRef}>
      {/* Modelo 3D do cérebro */}
      <Suspense fallback={null}>
        <BrainModel activityLevel={activityLevel} />
      </Suspense>

      {/* Glow externo - envelope luminoso ao redor do cérebro (reativo à coerência) */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[0.8, 32, 32]} />
        <meshBasicMaterial
          color="#00fff2"
          transparent
          opacity={0.04}
          side={THREE.BackSide}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* Glow interno mais intenso (pulsa durante sync) */}
      <mesh ref={innerGlowRef}>
        <sphereGeometry args={[0.65, 32, 32]} />
        <meshBasicMaterial
          color="#06b6d4"
          transparent
          opacity={0.02}
          side={THREE.BackSide}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* Neurônios internos */}
      {neurons.map((pos, i) => (
        <Neuron
          key={`neuron-${i}`}
          position={pos}
          active={activeNeurons.has(i)}
          delay={i * 0.1}
        />
      ))}

      {/* Sinapses conectando neurônios */}
      {connections.map(([startIdx, endIdx], i) => {
        const isActive =
          activeNeurons.has(startIdx) || activeNeurons.has(endIdx);
        return (
          <Synapse
            key={`synapse-${i}`}
            start={neurons[startIdx]}
            end={neurons[endIdx]}
            active={isActive}
            delay={i * 0.05}
          />
        );
      })}

      {/* Anel de energia horizontal - roda e intensifica com coerência */}
      <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.55, 0.57, 64]} />
        <meshBasicMaterial
          color="#00fff2"
          transparent
          opacity={0.25}
          side={THREE.DoubleSide}
          toneMapped={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
    </group>
  );
}

// Preload do modelo
useGLTF.preload("/brain.glb");
