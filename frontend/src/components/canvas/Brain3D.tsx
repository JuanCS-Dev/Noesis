"use client";

import { useRef, useMemo, Suspense } from "react";
import { useFrame } from "@react-three/fiber";
import { useGLTF, Line } from "@react-three/drei";
import * as THREE from "three";

/**
 * Neurônio interno - pulsa quando ativo
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

  useFrame((state) => {
    if (ref.current) {
      const t = state.clock.getElapsedTime() + delay;
      const pulse = active ? 1 + Math.sin(t * 8) * 0.4 : 1;
      ref.current.scale.setScalar(pulse);

      const material = ref.current.material as THREE.MeshStandardMaterial;
      if (active) {
        const intensity = 0.5 + Math.sin(t * 8) * 0.5;
        material.emissiveIntensity = intensity * 3;
      }
    }
  });

  return (
    <mesh ref={ref} position={position}>
      <sphereGeometry args={[0.025, 12, 12]} />
      <meshStandardMaterial
        color={active ? "#fbbf24" : "#22d3ee"}
        emissive={active ? "#fbbf24" : "#0891b2"}
        emissiveIntensity={active ? 2 : 0.5}
        transparent
        opacity={active ? 1 : 0.7}
        toneMapped={false}
      />
    </mesh>
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
 */
function generateNeuralPoints(count: number): THREE.Vector3[] {
  const points: THREE.Vector3[] = [];

  for (let i = 0; i < count; i++) {
    // Distribuição em elipsóide - ajustado para caber dentro do cérebro
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    const r = 0.4 + Math.random() * 0.25;

    // Elipsóide achatado no formato do cérebro
    const x = r * Math.sin(phi) * Math.cos(theta) * 1.2;
    const y = r * Math.sin(phi) * Math.sin(theta) * 0.8;
    const z = r * Math.cos(phi) * 0.7;

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
 * CENTRALIZADO NO ORIGIN [0,0,0]
 */
function BrainModel({ activityLevel = 0.3 }: { activityLevel?: number }) {
  const { scene } = useGLTF("/brain.glb");

  // CENTRALIZAR: mover a geometria para [0,0,0]
  useMemo(() => {
    // Calcular centro do modelo
    const box = new THREE.Box3().setFromObject(scene);
    const center = box.getCenter(new THREE.Vector3());

    // MOVER A SCENE INTEIRA para que o centro fique em [0,0,0]
    scene.position.set(-center.x, -center.y, -center.z);

    // Configurar materiais
    scene.traverse((child) => {
      if (child instanceof THREE.Points) {
        child.material = new THREE.PointsMaterial({
          color: "#00fff2",
          size: 0.02,
          transparent: true,
          opacity: 0.8,
          sizeAttenuation: true,
          depthWrite: false,
          blending: THREE.AdditiveBlending,
        });
      } else if (child instanceof THREE.Mesh) {
        child.material = new THREE.MeshPhysicalMaterial({
          color: "#0891b2",
          transparent: true,
          opacity: 0.3,
          transmission: 0.5,
          side: THREE.DoubleSide,
          emissive: "#064e63",
          emissiveIntensity: 0.3,
        });
      }
    });
  }, [scene]);

  // Animação de pulso
  useFrame((state) => {
    scene.traverse((child) => {
      if (child instanceof THREE.Points) {
        const material = child.material as THREE.PointsMaterial;
        const t = state.clock.getElapsedTime();
        material.size = 0.015 + Math.sin(t * 2) * 0.005 * activityLevel;
        material.opacity = 0.7 + Math.sin(t * 3) * 0.2 * activityLevel;
      }
    });
  });

  return (
    <primitive
      object={scene}
      scale={1.5}
    />
  );
}

/**
 * Brain3D - Cérebro 3D real com topologia neural interna
 */
export default function Brain3D({
  activityLevel = 0.3,
}: {
  activityLevel?: number;
}) {
  const groupRef = useRef<THREE.Group>(null);

  // Gerar neurônios e conexões dentro do cérebro
  const neurons = useMemo(() => generateNeuralPoints(60), []);
  const connections = useMemo(
    () => generateConnections(neurons, 0.4),
    [neurons]
  );

  // Quais neurônios estão ativos
  const activeNeurons = useMemo(() => {
    const active = new Set<number>();
    const count = Math.floor(neurons.length * activityLevel);
    while (active.size < count) {
      active.add(Math.floor(Math.random() * neurons.length));
    }
    return active;
  }, [neurons.length, activityLevel]);

  // Animação de rotação e pulso
  useFrame((state) => {
    if (groupRef.current) {
      // Rotação lenta
      groupRef.current.rotation.y = state.clock.getElapsedTime() * 0.15;

      // Breathing effect
      const breathe = 1 + Math.sin(state.clock.getElapsedTime() * 0.5) * 0.02;
      groupRef.current.scale.setScalar(breathe);
    }
  });

  return (
    <group ref={groupRef}>
      {/* Modelo 3D do cérebro */}
      <Suspense fallback={null}>
        <BrainModel activityLevel={activityLevel} />
      </Suspense>

      {/* Glow externo */}
      <mesh>
        <sphereGeometry args={[1.2, 32, 32]} />
        <meshBasicMaterial
          color="#00fff2"
          transparent
          opacity={0.03}
          side={THREE.BackSide}
          depthWrite={false}
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

      {/* Anel de energia horizontal */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.85, 0.88, 64]} />
        <meshBasicMaterial
          color="#00fff2"
          transparent
          opacity={0.2}
          side={THREE.DoubleSide}
          toneMapped={false}
        />
      </mesh>
    </group>
  );
}

// Preload do modelo
useGLTF.preload("/brain.glb");
