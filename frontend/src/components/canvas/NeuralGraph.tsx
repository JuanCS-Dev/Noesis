"use client";

import { useRef, useMemo, Suspense } from "react";
import { useFrame } from "@react-three/fiber";
import { Line, Sphere } from "@react-three/drei";
import * as THREE from "three";
import BrainOverlay from "./BrainOverlay";

function Node({ position, active }: { position: [number, number, number]; active: boolean }) {
  const ref = useRef<any>(null);
  
  useFrame((state) => {
    if (ref.current && active) {
      const t = state.clock.getElapsedTime();
      ref.current.scale.setScalar(1 + Math.sin(t * 10) * 0.2);
    }
  });

  return (
    <Sphere ref={ref} args={[0.06, 16, 16]} position={position}>
      <meshStandardMaterial 
        color={active ? "#f59e0b" : "#06b6d4"} 
        emissive={active ? "#f59e0b" : "#06b6d4"}
        emissiveIntensity={active ? 3 : 1.2}
        roughness={0.2}
        metalness={0.8}
        toneMapped={false}
      />
    </Sphere>
  );
}

function Synapse({ start, end, active }: { start: [number, number, number]; end: [number, number, number]; active: boolean }) {
  return (
    <Line 
      points={[start, end]} 
      color={active ? "#f59e0b" : "#0e7490"}
      lineWidth={active ? 2.5 : 1.5}
      transparent 
      opacity={active ? 0.9 : 0.4}
      toneMapped={false}
      dashed={false}
    />
  );
}

export default function NeuralGraph() {
  // Gerar topologia aleatória
  const nodes = useMemo(() => {
    const n = [];
    for(let i=0; i<20; i++) {
      n.push([
        (Math.random() - 0.5) * 4,
        (Math.random() - 0.5) * 4,
        (Math.random() - 0.5) * 2
      ] as [number, number, number]);
    }
    return n;
  }, []);

  const connections = useMemo(() => {
    const c = [];
    for(let i=0; i<nodes.length; i++) {
      for(let j=i+1; j<nodes.length; j++) {
        if(Math.random() > 0.8) { // Conexão esparsa
          c.push([i, j]);
        }
      }
    }
    return c;
  }, [nodes]);

  return (
    <group>
      {/* Cérebro holográfico no centro - conexões parecem acontecer dentro dele */}
      <Suspense fallback={null}>
        <BrainOverlay />
      </Suspense>

      {/* Nós neurais orbitando ao redor do cérebro */}
      {nodes.map((pos, i) => (
        <Node key={i} position={pos} active={i % 5 === 0} />
      ))}

      {/* Sinapses conectando os nós */}
      {connections.map(([startIdx, endIdx], i) => (
        <Synapse
          key={`link-${i}`}
          start={nodes[startIdx]}
          end={nodes[endIdx]}
          active={i % 7 === 0}
        />
      ))}
    </group>
  );
}
