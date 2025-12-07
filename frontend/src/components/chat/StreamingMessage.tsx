"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useConsciousnessStore } from "@/stores/consciousnessStore";

interface StreamingMessageProps {
  className?: string;
}

// Keywords to highlight with special styling
const HIGHLIGHT_KEYWORDS = [
  "consciousness", "consciente", "consciência",
  "awareness", "phenomenal", "qualia",
  "coherence", "coerência", "sync",
  "ignition", "ignição", "ESGT",
  "Kuramoto", "synchronization",
];

function highlightText(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;

  // Create regex for all keywords (case insensitive)
  const regex = new RegExp(`(${HIGHLIGHT_KEYWORDS.join("|")})`, "gi");
  let match;

  while ((match = regex.exec(text)) !== null) {
    // Add text before match
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    // Add highlighted match
    parts.push(
      <span key={match.index} className="text-cyan-400 font-semibold">
        {match[0]}
      </span>
    );
    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? parts : [text];
}

export default function StreamingMessage({ className = "" }: StreamingMessageProps) {
  const { tokens, isStreaming, currentPhase, coherence } = useConsciousnessStore();

  // Combine tokens into full text for highlighting
  const fullText = tokens.join("");

  return (
    <div className={`relative ${className}`}>
      {/* Message content */}
      <div className="text-gray-200 leading-relaxed font-mono text-sm">
        <AnimatePresence mode="popLayout">
          {tokens.map((token, index) => (
            <motion.span
              key={`token-${index}`}
              initial={{ opacity: 0, y: 8, filter: "blur(4px)" }}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              transition={{
                duration: 0.15,
                ease: "easeOut",
              }}
              className="inline"
            >
              {highlightText(token)}
            </motion.span>
          ))}
        </AnimatePresence>

        {/* Neural cursor */}
        {isStreaming && (
          <motion.span
            className="inline-block w-2 h-5 ml-0.5 bg-cyan-400 rounded-sm align-middle"
            animate={{
              opacity: [1, 0.3, 1],
              scaleY: [1, 0.8, 1],
              boxShadow: [
                "0 0 4px #22d3ee",
                "0 0 12px #22d3ee",
                "0 0 4px #22d3ee",
              ],
            }}
            transition={{
              duration: 0.8,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        )}
      </div>

      {/* Streaming indicator overlay */}
      {isStreaming && (
        <motion.div
          className="absolute -left-4 top-0 bottom-0 w-1 rounded-full"
          style={{
            background: `linear-gradient(to bottom,
              transparent 0%,
              ${coherence >= 0.7 ? "#22d3ee" : "#f59e0b"} 50%,
              transparent 100%
            )`,
          }}
          animate={{
            opacity: [0.3, 1, 0.3],
          }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
      )}

      {/* Phase badge */}
      {isStreaming && currentPhase !== "idle" && (
        <motion.div
          className="absolute -right-2 -top-2 px-2 py-0.5 rounded-full text-[8px] uppercase tracking-wider font-bold"
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          style={{
            backgroundColor:
              currentPhase === "synchronize" ? "rgba(34, 211, 238, 0.2)" :
              currentPhase === "broadcast" ? "rgba(168, 85, 247, 0.2)" :
              currentPhase === "sustain" ? "rgba(236, 72, 153, 0.2)" :
              "rgba(251, 191, 36, 0.2)",
            color:
              currentPhase === "synchronize" ? "#22d3ee" :
              currentPhase === "broadcast" ? "#a855f7" :
              currentPhase === "sustain" ? "#ec4899" :
              "#fbbf24",
            border: "1px solid currentColor",
          }}
        >
          {currentPhase}
        </motion.div>
      )}
    </div>
  );
}

// Standalone token-by-token component for custom use
export function TokenStream({ tokens, speed = 50 }: { tokens: string[]; speed?: number }) {
  return (
    <span className="inline">
      {tokens.map((token, i) => (
        <motion.span
          key={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: i * (speed / 1000) }}
        >
          {token}
        </motion.span>
      ))}
    </span>
  );
}
