"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Activity, Cpu, Shield, Zap, Wifi, WifiOff, Gavel, ChevronDown, ChevronUp, AlertTriangle } from "lucide-react";
import {
  useConsciousnessMetrics,
  deriveMetricsForUI,
} from "@/hooks/useConsciousnessMetrics";
import { useWebSocketConsciousness } from "@/hooks/useWebSocketConsciousness";
import { useConsciousnessStore } from "@/stores/consciousnessStore";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

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

const TribunalPanel = dynamic(
  () => import("@/components/tribunal/TribunalPanel"),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full text-slate-500">
        <Gavel className="w-6 h-6 text-amber-400 animate-pulse" />
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
 * ConnectionStatus - Indicador de conexão com o backend
 */
function ConnectionStatus({ isConnected }: { isConnected: boolean }) {
  return (
    <motion.div
      className={`flex items-center gap-1.5 px-2 py-1 rounded-full ${
        isConnected ? "bg-emerald-900/30" : "bg-red-900/30"
      }`}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
    >
      {isConnected ? (
        <>
          <motion.div
            className="w-2 h-2 rounded-full bg-emerald-400"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <Wifi className="w-3 h-3 text-emerald-400" />
        </>
      ) : (
        <>
          <div className="w-2 h-2 rounded-full bg-red-400" />
          <WifiOff className="w-3 h-3 text-red-400" />
        </>
      )}
      <span
        className={`text-[9px] uppercase tracking-wider ${
          isConnected ? "text-emerald-400" : "text-red-400"
        }`}
      >
        {isConnected ? "ONLINE" : "OFFLINE"}
      </span>
    </motion.div>
  );
}

/**
 * Home - Página principal do Daimon
 */
export default function Home() {
  const [activityLevel, setActivityLevel] = useState(0.3);
  const [showTribunal, setShowTribunal] = useState(false);

  // Fetch real metrics from MAXIMUS backend (polling)
  const { metrics, isConnected, isLoading } = useConsciousnessMetrics({
    pollingIntervalMs: 5000,
    enabled: true,
  });

  // WebSocket for real-time updates
  const { handleWSEvent, setWSStatus } = useConsciousnessStore();
  const { status: wsStatus } = useWebSocketConsciousness({
    enabled: true,
    onEvent: handleWSEvent,
  });

  // Sync WS status to store
  useEffect(() => {
    setWSStatus(wsStatus);
  }, [wsStatus, setWSStatus]);

  // Derive UI-friendly values
  const derivedMetrics = deriveMetricsForUI(metrics);

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
            <ConnectionStatus isConnected={isConnected} />
            <AnimatePresence mode="wait">
              {isLoading ? (
                <motion.div
                  key="loading"
                  className="flex items-center gap-2 px-3 py-1.5"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.5 }}
                  exit={{ opacity: 0 }}
                >
                  <div className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
                  <span className="text-[10px] text-slate-500">SYNCING...</span>
                </motion.div>
              ) : (
                <motion.div
                  key="metrics"
                  className="flex items-center gap-3"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <StatusMetric
                    icon={Shield}
                    label="Integrity"
                    value={
                      isConnected
                        ? `${derivedMetrics.integrityPercent}%`
                        : "--"
                    }
                    color={
                      derivedMetrics.isHealthy
                        ? "text-emerald-400"
                        : isConnected
                        ? "text-amber-400"
                        : "text-slate-500"
                    }
                  />
                  <StatusMetric
                    icon={Activity}
                    label="Arousal"
                    value={
                      isConnected
                        ? derivedMetrics.arousalLevel
                        : "OFFLINE"
                    }
                    color={
                      derivedMetrics.arousalLevel === "ACTIVE"
                        ? "text-amber-400"
                        : derivedMetrics.arousalLevel === "HIGH"
                        ? "text-red-400"
                        : "text-purple-400"
                    }
                  />
                  <StatusMetric
                    icon={Cpu}
                    label="Coherence"
                    value={
                      isConnected
                        ? `${derivedMetrics.coherencePercent}%`
                        : "--"
                    }
                    color="text-cyan-400"
                  />
                  {derivedMetrics.safetyViolations > 0 && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="flex items-center gap-1 px-2 py-1 bg-red-900/40 border border-red-500/50 rounded"
                    >
                      <Shield className="w-3 h-3 text-red-400" />
                      <span className="text-[10px] text-red-400 font-bold">
                        {derivedMetrics.safetyViolations} VIOLATIONS
                      </span>
                    </motion.div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
            <StatusMetric
              icon={Zap}
              label="Version"
              value="v4.0.1-α"
              color="text-slate-400"
            />
          </div>
        </motion.header>

        {/* Main Content */}
        <div className="flex-1 flex flex-col gap-4 p-4 overflow-hidden">
          {/* Top Row: Brain + Chat */}
          <div className="flex-1 flex gap-4 overflow-hidden min-h-0">
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
                <div className="flex items-center gap-3">
                  <span className="text-[10px] text-slate-600">
                    {isConnected ? derivedMetrics.neuronCount : "--"} neurônios |{" "}
                    {Math.round(activityLevel * 100)}% atividade
                  </span>
                  {/* WebSocket indicator */}
                  <div
                    className={`w-1.5 h-1.5 rounded-full ${
                      wsStatus === "connected"
                        ? "bg-emerald-400"
                        : wsStatus === "reconnecting"
                        ? "bg-amber-400 animate-pulse"
                        : "bg-slate-600"
                    }`}
                    title={`WebSocket: ${wsStatus}`}
                  />
                </div>
              </div>

              {/* 3D Canvas */}
              <div className="flex-1 relative">
                <ErrorBoundary
                  componentName="Neural Topology"
                  fallback={
                    <div className="flex flex-col items-center justify-center h-full text-slate-500">
                      <AlertTriangle className="w-8 h-8 text-amber-400 mb-2" />
                      <span className="text-xs">3D Rendering Unavailable</span>
                    </div>
                  }
                >
                  <TopologyPanel activityLevel={activityLevel} />
                </ErrorBoundary>

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
              className="flex-1 glass-panel rounded-xl overflow-hidden min-w-[400px] flex flex-col"
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
              <div className="flex-1 overflow-hidden">
                <ErrorBoundary componentName="Chat Interface">
                  <ChatInterface onActivityChange={setActivityLevel} />
                </ErrorBoundary>
              </div>
            </motion.div>
          </div>

          {/* Bottom: Tribunal Panel (collapsible) */}
          <motion.div
            className="flex-shrink-0"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            {/* Tribunal Toggle Button */}
            <button
              onClick={() => setShowTribunal(!showTribunal)}
              className="w-full flex items-center justify-center gap-2 py-2 glass-panel rounded-t-lg border-b-0 hover:bg-amber-900/10 transition-colors"
            >
              <Gavel className="w-4 h-4 text-amber-400" />
              <span className="text-xs uppercase tracking-wider text-amber-400 font-bold">
                Tribunal - The Three Judges
              </span>
              {showTribunal ? (
                <ChevronDown className="w-4 h-4 text-amber-400" />
              ) : (
                <ChevronUp className="w-4 h-4 text-amber-400" />
              )}
            </button>

            {/* Tribunal Panel Content */}
            <AnimatePresence>
              {showTribunal && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="overflow-hidden"
                >
                  <ErrorBoundary componentName="Tribunal Panel">
                    <TribunalPanel className="rounded-t-none" />
                  </ErrorBoundary>
                </motion.div>
              )}
            </AnimatePresence>
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
            <span
              className={
                derivedMetrics.isHealthy ? "text-cyan-400" : "text-amber-400"
              }
            >
              {isConnected
                ? (derivedMetrics.integrityPercent / 100).toFixed(2)
                : "--"}
            </span>
          </span>
        </motion.footer>
      </div>
    </main>
  );
}
