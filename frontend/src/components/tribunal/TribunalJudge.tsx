"use client";

import { motion } from "framer-motion";
import { Shield, Brain, Scale } from "lucide-react";
import type { JudgeConfig, JudgeVerdict } from "@/services/tribunalApi";

interface TribunalJudgeProps {
  config: JudgeConfig;
  verdict?: JudgeVerdict;
  isOnline: boolean;
  index: number;
}

const ICON_MAP = {
  shield: Shield,
  brain: Brain,
  scale: Scale,
};

/**
 * CircularGauge - Animated circular progress gauge
 */
function CircularGauge({
  value,
  color,
  size = 48,
}: {
  value: number;
  color: string;
  size?: number;
}) {
  const strokeWidth = 4;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - value * circumference;

  return (
    <svg width={size} height={size} className="transform -rotate-90">
      {/* Background circle */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="transparent"
        stroke="rgba(100, 116, 139, 0.2)"
        strokeWidth={strokeWidth}
      />
      {/* Progress circle */}
      <motion.circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="transparent"
        stroke={`var(--${color.replace("text-", "").replace("-400", "-glow")})`}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={circumference}
        initial={{ strokeDashoffset: circumference }}
        animate={{ strokeDashoffset: offset }}
        transition={{ duration: 1, ease: "easeOut" }}
        style={{
          filter: `drop-shadow(0 0 6px var(--${color.replace("text-", "").replace("-400", "-glow")}))`,
        }}
      />
      {/* Center value */}
      <text
        x={size / 2}
        y={size / 2}
        textAnchor="middle"
        dominantBaseline="central"
        className={`${color} text-xs font-bold`}
        style={{ transform: "rotate(90deg)", transformOrigin: "center" }}
      >
        {Math.round(value * 100)}%
      </text>
    </svg>
  );
}

/**
 * TribunalJudge - Individual judge card with animated gauge
 */
export default function TribunalJudge({
  config,
  verdict,
  isOnline,
  index,
}: TribunalJudgeProps) {
  const Icon = ICON_MAP[config.icon];
  const confidence = verdict?.confidence ?? 0;
  const passed = verdict?.passed ?? null;

  return (
    <motion.div
      className={`
        relative p-4 rounded-lg glass-panel
        ${config.color.border}
        ${config.color.bg}
        transition-all duration-300
      `}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      whileHover={{ scale: 1.02, y: -2 }}
    >
      {/* Status indicator */}
      <div className="absolute top-2 right-2">
        <motion.div
          className={`w-2 h-2 rounded-full ${
            isOnline
              ? passed === null
                ? "bg-slate-500"
                : passed
                ? "bg-emerald-400"
                : "bg-red-400"
              : "bg-slate-600"
          }`}
          animate={
            isOnline && passed !== null
              ? { opacity: [0.5, 1, 0.5] }
              : undefined
          }
          transition={{ duration: 2, repeat: Infinity }}
        />
      </div>

      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <motion.div
          className={`p-2 rounded-lg ${config.color.bg} border ${config.color.border}`}
          whileHover={{ rotate: [0, -10, 10, 0] }}
          transition={{ duration: 0.4 }}
        >
          <Icon className={`w-5 h-5 ${config.color.primary}`} />
        </motion.div>
        <div>
          <div className="flex items-center gap-2">
            <h3 className={`text-sm font-bold ${config.color.primary}`}>
              {config.name}
            </h3>
            <span className="text-base">{config.spiritualSymbol}</span>
          </div>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">
            {config.pillar}
          </p>
        </div>
      </div>

      {/* Gauge */}
      <div className="flex justify-center my-3">
        {isOnline ? (
          <CircularGauge value={confidence} color={config.color.primary} />
        ) : (
          <div className="w-12 h-12 flex items-center justify-center rounded-full border border-slate-700">
            <span className="text-xs text-slate-600">--</span>
          </div>
        )}
      </div>

      {/* Verdict */}
      <div className="text-center">
        {isOnline && verdict ? (
          <>
            <motion.div
              className={`
                inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-bold
                ${
                  passed
                    ? "bg-emerald-900/30 text-emerald-400 border border-emerald-500/30"
                    : "bg-red-900/30 text-red-400 border border-red-500/30"
                }
              `}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", delay: 0.3 + index * 0.1 }}
            >
              {passed ? "APPROVED" : "REJECTED"}
            </motion.div>
            {verdict.reasoning && (
              <p className="mt-2 text-[10px] text-slate-500 line-clamp-2">
                {verdict.reasoning}
              </p>
            )}
          </>
        ) : (
          <span className="text-[10px] text-slate-600 uppercase tracking-wider">
            {isOnline ? "Awaiting Input" : "Offline"}
          </span>
        )}
      </div>

      {/* Description */}
      <p className="mt-3 text-[9px] text-slate-600 text-center italic">
        {config.description}
      </p>
    </motion.div>
  );
}

