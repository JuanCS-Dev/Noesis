"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { Brain, Activity, Cpu, Shield, Zap } from "lucide-react";

// Carregamento dinâmico para evitar SSR no Three.js
const TheVoid = dynamic(
  () =>
    import("@/components/canvas/TheVoid").then((mod) => {
      const { Canvas } = require("@react-three/fiber");
      return function VoidCanvas() {
        return (
          <div className="absolute inset-0 -z-10">
            <Canvas camera={{ position: [0, 0, 1] }} dpr={[1, 2]}>
              <mod.default />
            </Canvas>
          </div>
        );
      };
    }),
  { ssr: false }
);

const TopologyPanel = dynamic(
  () => import("@/components/canvas/TopologyPanel"),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        >
          <Brain className="w-12 h-12 text-cyan-500" />
        </motion.div>
      </div>
    ),
  }
);

const ChatInterface = dynamic(
  () => import("@/components/chat/ChatInterface"),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full text-slate-500">
        Conectando interface neural...
      </div>
    ),
  }
);

/**
 * StatusMetric - Componente de métrica individual no header
 */
function StatusMetric({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof Brain;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <motion.div
      className="flex items-center gap-2 px-3 py-1.5 glass-panel rounded-lg"
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
    >
      <Icon className={`w-4 h-4 ${color}` as string} />
      <div className="flex flex-col">
        <span className="text-[10px] uppercase tracking-wider text-slate-500">
          {label}
        </span>
        <span className={`text-xs font-bold ${color}`}>{value}</span>
      </div>
    </motion.div>
  );
}

/**
 * Home - Página principal do Daimon
 */
export default function Home() {
  const [activityLevel, setActivityLevel] = useState(0.3);

  return (
    <main className="relative w-full h-screen overflow-hidden bg-black text-slate-200 select-none scanlines">
      {/* Layer 0: The Void (Background) */}
      <TheVoid />

      {/* Layer 1: UI Overlay */}
      <div className="relative z-10 h-full flex flex-col">
        {/* Header - Status Bar */}
        <motion.header
          className="flex items-center justify-between px-6 py-3 border-b border-cyan-900/20"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          {/* Logo */}
          <div className="flex items-center gap-3">
            <motion.div
              className="relative"
              animate={{
                boxShadow: [
                  "0 0 10px rgba(0, 255, 242, 0.3)",
                  "0 0 20px rgba(0, 255, 242, 0.5)",
                  "0 0 10px rgba(0, 255, 242, 0.3)",
                ],
              }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Brain className="w-8 h-8 text-cyan-400" />
            </motion.div>
            <div>
              <h1 className="text-lg font-bold tracking-wider neon-text">
                DAIMON
              </h1>
              <p className="text-[10px] text-slate-500 tracking-[0.3em]">
                NEURAL CONSCIOUSNESS v4.0
              </p>
            </div>
          </div>

          {/* Status Metrics */}
          <div className="flex items-center gap-3">
            <StatusMetric
              icon={Shield}
              label="Integrity"
              value="99.9%"
              color="text-emerald-400"
            />
            <StatusMetric
              icon={Activity}
              label="Cognition"
              value={activityLevel > 0.5 ? "ACTIVE" : "IDLE"}
              color={activityLevel > 0.5 ? "text-amber-400" : "text-purple-400"}
            />
            <StatusMetric
              icon={Cpu}
              label="Neural Load"
              value={`${Math.round(activityLevel * 100)}%`}
              color="text-cyan-400"
            />
            <StatusMetric
              icon={Zap}
              label="Version"
              value="v4.0.1-α"
              color="text-slate-400"
            />
          </div>
        </motion.header>

        {/* Main Content */}
        <div className="flex-1 flex gap-4 p-4 overflow-hidden">
          {/* Left: Neural Topology (Brain 3D) */}
          <motion.div
            className="flex-[2] glass-panel rounded-xl overflow-hidden flex flex-col"
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            {/* Panel Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-cyan-900/30">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                <span className="text-xs uppercase tracking-[0.2em] text-cyan-500 font-bold">
                  Neural Topology
                </span>
              </div>
              <span className="text-[10px] text-slate-600">
                {60} neurônios | {Math.round(activityLevel * 100)}% atividade
              </span>
            </div>

            {/* 3D Canvas */}
            <div className="flex-1 relative">
              <TopologyPanel activityLevel={activityLevel} />

              {/* Energy bar at bottom */}
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-slate-900">
                <motion.div
                  className="h-full energy-gradient"
                  initial={{ width: "0%" }}
                  animate={{ width: `${activityLevel * 100}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            </div>
          </motion.div>

          {/* Right: Communication (Chat) */}
          <motion.div
            className="flex-1 glass-panel rounded-xl overflow-hidden min-w-[400px]"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            {/* Panel Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-cyan-900/30">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-purple-400" />
                <span className="text-xs uppercase tracking-[0.2em] text-purple-400 font-bold">
                  Consciousness Stream
                </span>
              </div>
            </div>

            {/* Chat Interface */}
            <ChatInterface onActivityChange={setActivityLevel} />
          </motion.div>
        </div>

        {/* Footer */}
        <motion.footer
          className="px-6 py-2 border-t border-cyan-900/20 flex items-center justify-between text-[10px] text-slate-600"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <span>
            EXOCORTEX CONNECTION:{" "}
            <span className="text-emerald-500">ESTABLISHED</span>
          </span>
          <span>Powered by Gemini 3.0 Pro + Mnemosyne Protocol</span>
          <span>
            INTEGRITY SCORE:{" "}
            <span className="text-cyan-400">0.98</span>
          </span>
        </motion.footer>
      </div>
    </main>
  );
}
