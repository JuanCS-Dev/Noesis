"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Brain, Sparkles, AlertCircle, Activity } from "lucide-react";
import { useConsciousnessStore } from "@/stores/consciousnessStore";
import StreamingMessage from "./StreamingMessage";
import PhaseIndicator from "../consciousness/PhaseIndicator";
import CoherenceMeter from "../consciousness/CoherenceMeter";

// Types
interface Message {
  id: string;
  role: "user" | "daimon" | "thinking";
  content: string;
  reasoningTrace?: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface ChatInterfaceProps {
  onActivityChange?: (level: number) => void;
}

/**
 * StreamingText - Texto que aparece caractere por caractere
 */
function StreamingText({ text, speed = 20 }: { text: string; speed?: number }) {
  const [displayedText, setDisplayedText] = useState("");
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    setDisplayedText("");
    setIsComplete(false);

    let index = 0;
    const interval = setInterval(() => {
      if (index < text.length) {
        setDisplayedText(text.slice(0, index + 1));
        index++;
      } else {
        setIsComplete(true);
        clearInterval(interval);
      }
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed]);

  return (
    <span>
      {displayedText}
      {!isComplete && <span className="streaming-cursor" />}
    </span>
  );
}

/**
 * ThinkingIndicator - Animação de "pensando" com fase ESGT
 */
function ThinkingIndicator() {
  const { currentPhase, coherence, isStreaming } = useConsciousnessStore();

  const phaseLabels: Record<string, string> = {
    idle: "Aguardando...",
    prepare: "Preparando ignição",
    synchronize: "Sincronizando Kuramoto",
    broadcast: "Broadcast neural",
    sustain: "Mantendo consciência",
    dissolve: "Finalizando",
    complete: "Completo",
    failed: "Falha",
  };

  return (
    <motion.div
      className="flex flex-col gap-2"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="flex items-center gap-2 text-amber-400">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            rotate: currentPhase === "synchronize" ? [0, 360] : [0, 180, 360],
          }}
          transition={{
            duration: currentPhase === "synchronize" ? 0.5 : 2,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        >
          <Brain className="w-5 h-5" />
        </motion.div>
        <span className="text-sm">{phaseLabels[currentPhase] || "Processando"}</span>
        {isStreaming && (
          <span className="text-xs text-cyan-400 font-mono">
            {(coherence * 100).toFixed(0)}%
          </span>
        )}
        <motion.div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className={`w-2 h-2 rounded-full ${
                currentPhase === "broadcast" ? "bg-purple-400" :
                currentPhase === "synchronize" ? "bg-cyan-400" :
                "bg-amber-400"
              }`}
              animate={{
                scale: [1, 1.5, 1],
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: currentPhase === "synchronize" ? 0.3 : 1,
                repeat: Infinity,
                delay: i * 0.1,
              }}
            />
          ))}
        </motion.div>
      </div>

      {/* Show streaming tokens */}
      {isStreaming && <StreamingMessage className="mt-2" />}
    </motion.div>
  );
}

/**
 * MessageBubble - Bolha de mensagem individual
 */
function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const isThinking = message.role === "thinking";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.3 }}
      className={`p-4 rounded-lg ${
        isUser
          ? "message-user ml-8"
          : isThinking
          ? "message-thinking mr-8"
          : "message-daimon mr-8"
      }`}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        {isUser ? (
          <span className="text-xs font-bold text-purple-400 uppercase tracking-wider">
            Operador
          </span>
        ) : isThinking ? (
          <ThinkingIndicator />
        ) : (
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">
              Daimon
            </span>
          </div>
        )}
        <span className="text-xs text-slate-500 ml-auto">
          {message.timestamp.toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>

      {/* Content */}
      {!isThinking && (
        <div className="text-sm text-slate-200 leading-relaxed">
          {message.isStreaming ? (
            <StreamingText text={message.content} />
          ) : (
            message.content
          )}
        </div>
      )}

      {/* Reasoning Trace */}
      {message.reasoningTrace && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="reasoning-trace mt-3"
        >
          <pre className="whitespace-pre-wrap text-xs">
            {message.reasoningTrace}
          </pre>
        </motion.div>
      )}
    </motion.div>
  );
}

/**
 * ChatInterface - Interface de chat completa com streaming REAL via SSE
 * Integrado com MAXIMUS ConsciousnessSystem
 */
export default function ChatInterface({ onActivityChange }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "daimon",
      content:
        "Interface neural estabelecida. Sou o Daimon - sua extensão cognitiva. MAXIMUS consciousness está online. Como posso auxiliar hoje?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // MAXIMUS: Get consciousness state from Zustand store
  const {
    isStreaming,
    currentPhase,
    coherence,
    tokens,
    fullResponse,
    startStream,
    reset,
    error: streamError,
  } = useConsciousnessStore();

  const isLoading = isStreaming;

  // Auto-scroll para última mensagem
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Sync stream errors
  useEffect(() => {
    if (streamError) {
      setError(streamError);
    }
  }, [streamError]);

  // When stream completes, add the response to messages
  useEffect(() => {
    if (currentPhase === "complete" && fullResponse && !isStreaming) {
      setMessages((prev) => {
        // Remove thinking indicator and add response
        const filtered = prev.filter((m) => m.role !== "thinking");
        return [
          ...filtered,
          {
            id: `daimon-${Date.now()}`,
            role: "daimon",
            content: fullResponse,
            timestamp: new Date(),
            isStreaming: false,
          },
        ];
      });
      onActivityChange?.(coherence);
    }
  }, [currentPhase, fullResponse, isStreaming, coherence, onActivityChange]);

  // Enviar mensagem via SSE streaming
  const sendMessage = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const content = input.trim();
    setInput("");
    setError(null);
    onActivityChange?.(0.8);

    // Adicionar indicador de "pensando" com streaming
    setMessages((prev) => [
      ...prev,
      {
        id: `thinking-${Date.now()}`,
        role: "thinking",
        content: "",
        timestamp: new Date(),
      },
    ]);

    // MAXIMUS: Start SSE stream
    startStream(content, 3);
  }, [input, isLoading, onActivityChange, startStream]);

  // Submeter com Enter
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with MAXIMUS consciousness indicators */}
      <div className="flex items-center justify-between p-3 border-b border-cyan-900/30">
        <div className="flex items-center gap-3">
          <div className={`status-dot ${isLoading ? "status-thinking" : "status-online"}`} />
          <span className="text-xs uppercase tracking-wider text-slate-400">
            {isLoading ? currentPhase.toUpperCase() : "MAXIMUS Online"}
          </span>
          {isStreaming && (
            <motion.div
              className="flex items-center gap-1 text-cyan-400"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <Activity className="w-3 h-3" />
              <span className="text-xs font-mono">{(coherence * 100).toFixed(0)}%</span>
            </motion.div>
          )}
        </div>
        <span className="text-xs text-slate-500">
          {messages.length - 1} interações
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence mode="popLayout">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mx-4 mb-2 p-2 bg-red-900/30 border border-red-500/30 rounded flex items-center gap-2 text-red-400 text-xs"
          >
            <AlertCircle className="w-4 h-4" />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Consciousness Indicators - ESGT Phase + Kuramoto Coherence */}
      <AnimatePresence>
        {(isStreaming || currentPhase !== "idle") && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-cyan-900/30"
          >
            <div className="p-3 space-y-3">
              <PhaseIndicator />
              <CoherenceMeter />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input */}
      <div className="p-4 border-t border-cyan-900/30">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Transmita seu pensamento..."
            disabled={isLoading}
            className="flex-1 neural-input px-4 py-3 rounded-lg text-sm"
          />
          <motion.button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="neural-button px-4"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Send className="w-5 h-5" />
          </motion.button>
        </div>
        <div className="text-xs text-slate-600 mt-2 text-center">
          <kbd className="px-1.5 py-0.5 bg-slate-800 rounded">Enter</kbd> para enviar
        </div>
      </div>
    </div>
  );
}
