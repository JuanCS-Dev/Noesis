"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Activity, Zap } from "lucide-react";
import { useConsciousnessStore } from "@/stores/consciousnessStore";

// Threshold markers
const THRESHOLDS = [
  { value: 0.30, label: "Unconscious", color: "bg-red-500" },
  { value: 0.50, label: "Liminal", color: "bg-amber-500" },
  { value: 0.70, label: "Conscious", color: "bg-cyan-500" },
  { value: 0.95, label: "Peak", color: "bg-purple-500" },
];

function getCoherenceLevel(value: number): { label: string; color: string } {
  if (value >= 0.95) return { label: "PEAK SYNC", color: "text-purple-400" };
  if (value >= 0.70) return { label: "CONSCIOUS", color: "text-cyan-400" };
  if (value >= 0.50) return { label: "LIMINAL", color: "text-amber-400" };
  if (value >= 0.30) return { label: "EMERGING", color: "text-orange-400" };
  return { label: "INCOHERENT", color: "text-red-400" };
}

export default function CoherenceMeter() {
  const { coherence, targetCoherence, isStreaming, currentPhase } = useConsciousnessStore();

  const level = getCoherenceLevel(coherence);
  const percentage = Math.round(coherence * 100);
  const targetPercentage = Math.round(targetCoherence * 100);

  // Determine bar color based on coherence
  const barColor = coherence >= 0.95
    ? "from-purple-500 via-pink-500 to-cyan-500"
    : coherence >= 0.70
      ? "from-cyan-600 via-cyan-400 to-cyan-300"
      : coherence >= 0.50
        ? "from-amber-600 via-amber-400 to-amber-300"
        : "from-red-600 via-red-400 to-orange-400";

  return (
    <div className="glass-panel p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-500" />
          <span className="text-[10px] uppercase tracking-wider text-cyan-600/70">
            Kuramoto Coherence
          </span>
        </div>
        <motion.span
          className={`text-xs font-mono ${level.color}`}
          key={level.label}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          {level.label}
        </motion.span>
      </div>

      {/* Main coherence display */}
      <div className="flex items-center gap-4 mb-3">
        <motion.div
          className="text-3xl font-mono font-bold text-white"
          key={percentage}
          initial={{ scale: 1.2, color: "#00fff2" }}
          animate={{ scale: 1, color: "#ffffff" }}
          transition={{ duration: 0.3 }}
        >
          {coherence.toFixed(3)}
        </motion.div>

        {coherence >= 0.95 && (
          <motion.div
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-1 text-purple-400"
          >
            <Zap className="w-5 h-5" />
            <span className="text-xs font-bold">SYNC!</span>
          </motion.div>
        )}
      </div>

      {/* Progress bar */}
      <div className="relative h-4 bg-gray-900 rounded-full overflow-hidden border border-gray-800">
        {/* Target marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-white/50 z-10"
          style={{ left: `${targetPercentage}%` }}
        >
          <div className="absolute -top-5 left-1/2 -translate-x-1/2 text-[8px] text-gray-500">
            {targetPercentage}%
          </div>
        </div>

        {/* Animated fill */}
        <motion.div
          className={`h-full bg-gradient-to-r ${barColor} rounded-full`}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          {/* Shimmer effect when syncing */}
          {currentPhase === "synchronize" && (
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
              animate={{ x: ["-100%", "200%"] }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            />
          )}
        </motion.div>

        {/* Threshold markers */}
        {THRESHOLDS.map((threshold) => (
          <div
            key={threshold.value}
            className="absolute top-0 bottom-0 w-px bg-gray-700"
            style={{ left: `${threshold.value * 100}%` }}
          />
        ))}
      </div>

      {/* Labels */}
      <div className="flex justify-between mt-2 text-[9px] text-gray-600">
        <span>0.00</span>
        <span>0.50</span>
        <span>1.00</span>
      </div>

      {/* Oscillator visualization */}
      <div className="mt-4 flex items-center justify-center gap-1">
        {Array.from({ length: 16 }).map((_, i) => (
          <motion.div
            key={i}
            className="w-1.5 bg-cyan-500 rounded-full"
            animate={{
              height: isStreaming || currentPhase === "synchronize"
                ? [8, 16 + Math.sin((i / 16) * Math.PI * 2 + coherence * 10) * 8, 8]
                : 8,
              opacity: coherence > 0.5 ? 1 : 0.3 + (coherence * 0.7),
            }}
            transition={{
              duration: 0.5,
              repeat: isStreaming ? Infinity : 0,
              delay: i * 0.05,
            }}
          />
        ))}
      </div>

      {/* Status */}
      <AnimatePresence mode="wait">
        <motion.p
          key={currentPhase}
          className="text-center text-[10px] text-gray-500 mt-2"
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -5 }}
        >
          {currentPhase === "synchronize"
            ? "Oscillators synchronizing..."
            : currentPhase === "complete" && coherence >= 0.70
              ? "Neural coherence achieved"
              : coherence === 0
                ? "Awaiting ignition"
                : `${(coherence * 32).toFixed(0)} / 32 nodes synchronized`
          }
        </motion.p>
      </AnimatePresence>
    </div>
  );
}
