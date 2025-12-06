"use client";

import { Canvas } from "@react-three/fiber";
import { View, Preload } from "@react-three/drei";
import TheVoid from "./TheVoid";
import NeuralGraph from "./NeuralGraph";

export default function Scene() {
  return (
    <Canvas
      className="absolute top-0 left-0 w-full h-full pointer-events-none"
      eventSource={typeof document !== "undefined" ? document.getElementById("root")! : undefined}
      dpr={[1, 2]}
      gl={{ 
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
        preserveDrawingBuffer: true,
        stencil: false,
        depth: true
      }}
      camera={{ position: [0, 0, 5], fov: 60 }}
    >
      {/* Background Layer */}
      <TheVoid />
      
      {/* Viewports tracking DOM elements */}
      <View.Port />
      <Preload all />
    </Canvas>
  );
}
