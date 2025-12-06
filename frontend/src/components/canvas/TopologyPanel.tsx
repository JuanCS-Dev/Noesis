"use client";

import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { PerspectiveCamera, OrbitControls, Environment } from "@react-three/drei";
import Brain3D from "@/components/canvas/Brain3D";

interface TopologyPanelProps {
  activityLevel?: number;
}

/**
 * TopologyPanel - Container para o cérebro 3D com topologia neural
 */
export default function TopologyPanel({ activityLevel = 0.3 }: TopologyPanelProps) {
  return (
    <div className="w-full h-full min-h-[300px] relative">
      <Canvas
        dpr={[1, 2]}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: "high-performance",
          toneMapping: 3, // ACESFilmicToneMapping
        }}
        className="absolute inset-0"
      >
        <PerspectiveCamera makeDefault position={[0, 0, 3]} fov={50} />
        <OrbitControls
          enableZoom={true}
          enablePan={false}
          autoRotate
          autoRotateSpeed={0.3}
          minDistance={2}
          maxDistance={8}
        />

        {/* Iluminação ambiente */}
        <ambientLight intensity={0.3} />

        {/* Luz principal - frontal */}
        <pointLight
          position={[5, 5, 5]}
          intensity={1}
          color="#ffffff"
        />

        {/* Luz secundária - roxa para profundidade */}
        <pointLight
          position={[-5, -5, -5]}
          intensity={0.6}
          color="#7c3aed"
        />

        {/* Luz de destaque - cyan */}
        <pointLight
          position={[0, 5, 0]}
          intensity={0.4}
          color="#00fff2"
        />

        {/* Cérebro 3D com topologia neural */}
        <Suspense fallback={null}>
          <Brain3D activityLevel={activityLevel} />
        </Suspense>
      </Canvas>

      {/* Overlay de canto - Label */}
      <div className="absolute top-3 right-3 text-[10px] text-cyan-600/50 uppercase tracking-wider">
        DRAG TO ROTATE | SCROLL TO ZOOM
      </div>
    </div>
  );
}
