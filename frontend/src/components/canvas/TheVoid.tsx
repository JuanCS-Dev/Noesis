"use client";

import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { Points, PointMaterial } from "@react-three/drei";
// @ts-ignore
import * as random from "maath/random/dist/maath-random.esm";

/**
 * StarLayer - Uma camada de estrelas com cor e velocidade específicas
 */
function StarLayer({
  count,
  radius,
  color,
  size,
  speed,
}: {
  count: number;
  radius: number;
  color: string;
  size: number;
  speed: number;
}) {
  const ref = useRef<any>(null);

  const positions = useMemo(() => {
    const data = new Float32Array(count * 3);
    random.inSphere(data, { radius });
    return data;
  }, [count, radius]);

  useFrame((_, delta) => {
    if (ref.current) {
      ref.current.rotation.x -= delta * speed * 0.1;
      ref.current.rotation.y -= delta * speed * 0.15;
    }
  });

  return (
    <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color={color}
        size={size}
        sizeAttenuation={true}
        depthWrite={false}
        opacity={0.8}
      />
    </Points>
  );
}

/**
 * NeuralWave - Ondas de energia no background
 */
function NeuralWave() {
  const ref = useRef<any>(null);

  const positions = useMemo(() => {
    const data = new Float32Array(300 * 3);
    for (let i = 0; i < 300; i++) {
      const angle = (i / 300) * Math.PI * 2;
      const r = 1.2 + Math.random() * 0.3;
      data[i * 3] = Math.cos(angle) * r;
      data[i * 3 + 1] = (Math.random() - 0.5) * 0.1;
      data[i * 3 + 2] = Math.sin(angle) * r;
    }
    return data;
  }, []);

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.getElapsedTime() * 0.1;
      // Pulso de escala
      const scale = 1 + Math.sin(state.clock.getElapsedTime() * 0.5) * 0.1;
      ref.current.scale.setScalar(scale);
    }
  });

  return (
    <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#00fff2"
        size={0.005}
        sizeAttenuation={true}
        depthWrite={false}
        opacity={0.4}
      />
    </Points>
  );
}

/**
 * TheVoid - Background com múltiplas camadas de partículas
 */
export default function TheVoid() {
  return (
    <group rotation={[0, 0, Math.PI / 4]}>
      {/* Camada distante - estrelas pequenas e lentas */}
      <StarLayer
        count={4000}
        radius={2}
        color="#ffffff"
        size={0.001}
        speed={0.2}
      />

      {/* Camada média - estrelas cyan */}
      <StarLayer
        count={2000}
        radius={1.5}
        color="#06b6d4"
        size={0.002}
        speed={0.4}
      />

      {/* Camada próxima - estrelas roxas */}
      <StarLayer
        count={1000}
        radius={1}
        color="#a855f7"
        size={0.003}
        speed={0.6}
      />

      {/* Anel neural pulsante */}
      <NeuralWave />
    </group>
  );
}
