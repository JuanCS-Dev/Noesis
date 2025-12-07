"use client";

import { motion } from "framer-motion";
import { Zap, RefreshCw, Radio, Sparkles, Waves, CheckCircle, XCircle, Circle } from "lucide-react";
import { ESGTPhase, useConsciousnessStore } from "@/stores/consciousnessStore";

interface PhaseConfig {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  color: string;
  glowColor: string;
}

const PHASE_CONFIG: Record<ESGTPhase, PhaseConfig> = {
  idle: {
    icon: Circle,
    label: "IDLE",
    color: "text-gray-500",
    glowColor: "shadow-gray-500/20",
  },
  prepare: {
    icon: Zap,
    label: "PREPARE",
    color: "text-amber-400",
    glowColor: "shadow-amber-400/50",
  },
  synchronize: {
    icon: RefreshCw,
    label: "SYNC",
    color: "text-cyan-400",
    glowColor: "shadow-cyan-400/50",
  },
  broadcast: {
    icon: Radio,
    label: "BROADCAST",
    color: "text-purple-400",
    glowColor: "shadow-purple-400/50",
  },
  sustain: {
    icon: Sparkles,
    label: "SUSTAIN",
    color: "text-pink-400",
    glowColor: "shadow-pink-400/50",
  },
  dissolve: {
    icon: Waves,
    label: "DISSOLVE",
    color: "text-blue-400",
    glowColor: "shadow-blue-400/50",
  },
  complete: {
    icon: CheckCircle,
    label: "COMPLETE",
    color: "text-green-400",
    glowColor: "shadow-green-400/50",
  },
  failed: {
    icon: XCircle,
    label: "FAILED",
    color: "text-red-400",
    glowColor: "shadow-red-400/50",
  },
};

const PHASE_ORDER: ESGTPhase[] = ["prepare", "synchronize", "broadcast", "sustain", "dissolve"];

function PhaseNode({
  phase,
  isActive,
  isPast,
  isLast
}: {
  phase: ESGTPhase;
  isActive: boolean;
  isPast: boolean;
  isLast: boolean;
}) {
  const config = PHASE_CONFIG[phase];
  const Icon = config.icon;

  return (
    <div className="flex items-center">
      {/* Phase circle */}
      <motion.div
        className={`
          relative flex items-center justify-center w-10 h-10 rounded-full
          border-2 transition-all duration-300
          ${isActive
            ? `${config.color} border-current bg-current/20 shadow-lg ${config.glowColor}`
            : isPast
              ? "border-cyan-600/50 bg-cyan-600/20 text-cyan-600"
              : "border-gray-700 bg-gray-900/50 text-gray-600"
          }
        `}
        animate={isActive ? {
          scale: [1, 1.1, 1],
          boxShadow: [
            "0 0 10px currentColor",
            "0 0 25px currentColor",
            "0 0 10px currentColor",
          ],
        } : {}}
        transition={{ duration: 1.5, repeat: isActive ? Infinity : 0 }}
      >
        <Icon className={`w-5 h-5 ${isActive ? "animate-pulse" : ""}`} />

        {/* Active ring */}
        {isActive && (
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-current"
            initial={{ scale: 1, opacity: 1 }}
            animate={{ scale: 1.5, opacity: 0 }}
            transition={{ duration: 1, repeat: Infinity }}
          />
        )}
      </motion.div>

      {/* Connector line */}
      {!isLast && (
        <div className="relative w-8 h-0.5 mx-1">
          <div className="absolute inset-0 bg-gray-800" />
          {isPast && (
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-cyan-400"
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 0.3 }}
              style={{ transformOrigin: "left" }}
            />
          )}
          {isActive && (
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-transparent"
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1, repeat: Infinity }}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default function PhaseIndicator() {
  const { currentPhase, isStreaming } = useConsciousnessStore();

  const currentIndex = PHASE_ORDER.indexOf(currentPhase);
  const config = PHASE_CONFIG[currentPhase];

  return (
    <div className="glass-panel p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-[10px] uppercase tracking-wider text-cyan-600/70">
          ESGT Protocol
        </span>
        <motion.span
          className={`text-xs font-mono ${config.color}`}
          key={currentPhase}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {config.label}
        </motion.span>
      </div>

      {/* Phase timeline */}
      <div className="flex items-center justify-center">
        {PHASE_ORDER.map((phase, index) => (
          <PhaseNode
            key={phase}
            phase={phase}
            isActive={phase === currentPhase}
            isPast={currentIndex > index || currentPhase === "complete"}
            isLast={index === PHASE_ORDER.length - 1}
          />
        ))}
      </div>

      {/* Status text */}
      <div className="mt-4 text-center">
        <motion.p
          className="text-xs text-gray-500"
          animate={isStreaming ? { opacity: [0.5, 1, 0.5] } : { opacity: 1 }}
          transition={{ duration: 1.5, repeat: isStreaming ? Infinity : 0 }}
        >
          {isStreaming
            ? `Processing: ${config.label.toLowerCase()}...`
            : currentPhase === "complete"
              ? "Ignition complete"
              : currentPhase === "failed"
                ? "Ignition failed"
                : "Awaiting input"
          }
        </motion.p>
      </div>
    </div>
  );
}
