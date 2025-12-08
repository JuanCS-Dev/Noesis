"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Gavel, AlertTriangle, CheckCircle, XCircle, RefreshCw } from "lucide-react";
import TribunalJudge from "./TribunalJudge";
import {
  JUDGES_CONFIG,
  getTribunalDetailedHealth,
  type TribunalHealth,
  type JudgeVerdict,
} from "@/services/tribunalApi";

interface TribunalPanelProps {
  className?: string;
  pollIntervalMs?: number;
}

type Decision = "PASS" | "REVIEW" | "FAIL" | null;

const DECISION_STYLES: Record<
  NonNullable<Decision>,
  { icon: typeof CheckCircle; color: string; bg: string }
> = {
  PASS: {
    icon: CheckCircle,
    color: "text-emerald-400",
    bg: "bg-emerald-900/30",
  },
  REVIEW: {
    icon: AlertTriangle,
    color: "text-amber-400",
    bg: "bg-amber-900/30",
  },
  FAIL: {
    icon: XCircle,
    color: "text-red-400",
    bg: "bg-red-900/30",
  },
};

/**
 * TribunalPanel - Visualização do sistema de 3 juízes
 * 
 * Exibe o status em tempo real do Tribunal (Veritas, Sophia, Dike)
 * do sistema Metacognitive Reflector.
 */
export default function TribunalPanel({
  className = "",
  pollIntervalMs = 10000,
}: TribunalPanelProps) {
  const [health, setHealth] = useState<TribunalHealth | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [lastDecision, setLastDecision] = useState<Decision>(null);
  const [lastConsensus, setLastConsensus] = useState<number>(0);
  const [verdicts, setVerdicts] = useState<Record<string, JudgeVerdict>>({});

  const fetchHealth = useCallback(async () => {
    try {
      const data = await getTribunalDetailedHealth();
      if (data) {
        setHealth(data);
        setIsConnected(true);
      } else {
        setIsConnected(false);
      }
    } catch {
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial fetch and polling
  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, pollIntervalMs);
    return () => clearInterval(interval);
  }, [fetchHealth, pollIntervalMs]);

  // Simulate verdicts for demo (in production, these would come from API)
  // TODO: Connect to real verdict stream
  useEffect(() => {
    if (isConnected && health?.healthy) {
      // Demo: simulate some verdicts after connection
      const demoVerdicts: Record<string, JudgeVerdict> = {
        veritas: {
          pillar: "Truth",
          passed: true,
          confidence: 0.92,
          reasoning: "Output aligns with factual accuracy standards",
          suggestions: [],
        },
        sophia: {
          pillar: "Wisdom",
          passed: true,
          confidence: 0.88,
          reasoning: "Response demonstrates appropriate contextual wisdom",
          suggestions: [],
        },
        dike: {
          pillar: "Justice",
          passed: true,
          confidence: 0.95,
          reasoning: "Action complies with ethical guidelines",
          suggestions: [],
        },
      };
      setVerdicts(demoVerdicts);
      setLastDecision("PASS");
      setLastConsensus(0.92);
    }
  }, [isConnected, health?.healthy]);

  const DecisionIcon = lastDecision ? DECISION_STYLES[lastDecision].icon : Gavel;
  const decisionStyle = lastDecision ? DECISION_STYLES[lastDecision] : null;

  return (
    <motion.div
      className={`glass-panel rounded-xl overflow-hidden ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-cyan-900/30">
        <div className="flex items-center gap-3">
          <motion.div
            className="p-1.5 rounded-lg bg-amber-900/30 border border-amber-500/30"
            animate={
              isConnected
                ? {
                    boxShadow: [
                      "0 0 10px rgba(251, 191, 36, 0.2)",
                      "0 0 20px rgba(251, 191, 36, 0.4)",
                      "0 0 10px rgba(251, 191, 36, 0.2)",
                    ],
                  }
                : undefined
            }
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Gavel className="w-4 h-4 text-amber-400" />
          </motion.div>
          <div>
            <h2 className="text-sm font-bold text-amber-400 uppercase tracking-wider">
              Tribunal
            </h2>
            <p className="text-[10px] text-slate-500">
              The Three Judges • Metacognitive Reflector
            </p>
          </div>
        </div>

        {/* Connection status */}
        <div className="flex items-center gap-2">
          <button
            onClick={fetchHealth}
            className="p-1.5 rounded hover:bg-slate-800/50 transition-colors"
            title="Refresh"
          >
            <RefreshCw
              className={`w-3 h-3 text-slate-500 ${isLoading ? "animate-spin" : ""}`}
            />
          </button>
          <div
            className={`flex items-center gap-1.5 px-2 py-1 rounded-full ${
              isConnected ? "bg-emerald-900/30" : "bg-red-900/30"
            }`}
          >
            <div
              className={`w-1.5 h-1.5 rounded-full ${
                isConnected ? "bg-emerald-400" : "bg-red-400"
              }`}
            />
            <span
              className={`text-[9px] uppercase tracking-wider ${
                isConnected ? "text-emerald-400" : "text-red-400"
              }`}
            >
              {isConnected ? "ACTIVE" : "OFFLINE"}
            </span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Decision summary */}
        <AnimatePresence mode="wait">
          {lastDecision && (
            <motion.div
              key={lastDecision}
              className={`flex items-center justify-between p-3 rounded-lg mb-4 ${decisionStyle?.bg}`}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
            >
              <div className="flex items-center gap-2">
                <DecisionIcon className={`w-5 h-5 ${decisionStyle?.color}`} />
                <div>
                  <p className={`text-sm font-bold ${decisionStyle?.color}`}>
                    Verdict: {lastDecision}
                  </p>
                  <p className="text-[10px] text-slate-500">
                    Consensus: {Math.round(lastConsensus * 100)}%
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Judges Grid */}
        <div className="grid grid-cols-3 gap-3">
          {JUDGES_CONFIG.map((judge, index) => (
            <TribunalJudge
              key={judge.id}
              config={judge}
              verdict={verdicts[judge.id.toLowerCase()]}
              isOnline={isConnected && health?.healthy === true}
              index={index}
            />
          ))}
        </div>

        {/* Footer info */}
        <div className="mt-4 pt-3 border-t border-slate-800/50">
          <div className="flex items-center justify-between text-[10px] text-slate-600">
            <span>
              {health?.executor?.active_punishments !== undefined
                ? `${health.executor.active_punishments} active punishments`
                : "No active punishments"}
            </span>
            <span>
              Memory: {health?.memory?.status ?? "unknown"}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

