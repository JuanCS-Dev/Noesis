"use client";

import { useRef } from "react";
import { useFrame, useLoader } from "@react-three/fiber";
import { Billboard } from "@react-three/drei";
import * as THREE from "three";

/**
 * BrainOverlay - Cérebro holográfico no centro do grafo neural.
 *
 * Usa Billboard para sempre encarar a câmera, criando ilusão 3D
 * mesmo com imagem 2D. O glow pulsa suavemente.
 */
export default function BrainOverlay() {
  const groupRef = useRef<THREE.Group>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  // Carregar textura do cérebro
  const texture = useLoader(THREE.TextureLoader, "/brain.png");
  texture.colorSpace = THREE.SRGBColorSpace;

  // Animação de pulso e glow
  useFrame((state) => {
    const t = state.clock.getElapsedTime();

    if (groupRef.current) {
      // Breathing effect suave
      const breathe = 1 + Math.sin(t * 0.8) * 0.03;
      groupRef.current.scale.setScalar(breathe);
    }

    if (glowRef.current) {
      // Glow pulsa com cor variando
      const glowIntensity = 0.06 + Math.sin(t * 1.5) * 0.02;
      (glowRef.current.material as THREE.MeshBasicMaterial).opacity = glowIntensity;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Glow esférico externo */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[1.8, 32, 32]} />
        <meshBasicMaterial
          color="#06b6d4"
          transparent
          opacity={0.06}
          side={THREE.BackSide}
          depthWrite={false}
        />
      </mesh>

      {/* Glow interno mais intenso */}
      <mesh>
        <sphereGeometry args={[1.2, 32, 32]} />
        <meshBasicMaterial
          color="#0891b2"
          transparent
          opacity={0.04}
          side={THREE.BackSide}
          depthWrite={false}
        />
      </mesh>

      {/* Cérebro - Billboard sempre de frente */}
      <Billboard follow={true} lockX={false} lockY={false} lockZ={false}>
        <mesh>
          <planeGeometry args={[3.2, 3.2]} />
          <meshBasicMaterial
            map={texture}
            transparent
            opacity={0.4}
            depthWrite={false}
            blending={THREE.AdditiveBlending}
          />
        </mesh>
      </Billboard>

      {/* Anel de energia ao redor */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[1.5, 1.55, 64]} />
        <meshBasicMaterial
          color="#06b6d4"
          transparent
          opacity={0.15}
          side={THREE.DoubleSide}
          depthWrite={false}
        />
      </mesh>
    </group>
  );
}
