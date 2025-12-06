"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Brain, Sparkles, AlertCircle } from "lucide-react";

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
 * ThinkingIndicator - Animação de "pensando"
 */
function ThinkingIndicator() {
  return (
    <motion.div
      className="flex items-center gap-2 text-amber-400"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          rotate: [0, 180, 360],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        <Brain className="w-5 h-5" />
      </motion.div>
      <span className="text-sm">Processando consciência</span>
      <motion.div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="w-2 h-2 bg-amber-400 rounded-full"
            animate={{
              scale: [1, 1.5, 1],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
              delay: i * 0.2,
            }}
          />
        ))}
      </motion.div>
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
 * ChatInterface - Interface de chat completa com streaming
 */
export default function ChatInterface({ onActivityChange }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "daimon",
      content:
        "Interface neural estabelecida. Sou o Daimon - sua extensão cognitiva. Como posso auxiliar na expansão da sua consciência hoje?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll para última mensagem
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Enviar mensagem
  const sendMessage = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);
    onActivityChange?.(0.8); // Alta atividade

    // Adicionar indicador de "pensando"
    const thinkingId = `thinking-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: thinkingId,
        role: "thinking",
        content: "",
        timestamp: new Date(),
      },
    ]);

    try {
      // Chamar API do backend
      const response = await fetch("http://localhost:8001/v1/exocortex/journal", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content: userMessage.content,
          timestamp: new Date().toISOString(),
          analysis_mode: "standard",
        }),
      });

      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Remover indicador de pensando
      setMessages((prev) => prev.filter((m) => m.id !== thinkingId));

      // Adicionar resposta do Daimon com streaming
      const daimonMessage: Message = {
        id: `daimon-${Date.now()}`,
        role: "daimon",
        content: data.response || "Processamento concluído.",
        reasoningTrace: data.reasoning_trace,
        timestamp: new Date(),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, daimonMessage]);

      // Após streaming terminar, marcar como completo
      setTimeout(() => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === daimonMessage.id ? { ...m, isStreaming: false } : m
          )
        );
      }, daimonMessage.content.length * 20 + 500);

    } catch (err) {
      // Remover indicador de pensando
      setMessages((prev) => prev.filter((m) => m.id !== thinkingId));

      setError(err instanceof Error ? err.message : "Erro desconhecido");

      // Mensagem de erro
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "daimon",
          content: "Falha na conexão neural. Verifique se o backend está ativo.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
      onActivityChange?.(0.3); // Atividade normal
    }
  }, [input, isLoading, onActivityChange]);

  // Submeter com Enter
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-cyan-900/30">
        <div className="flex items-center gap-2">
          <div className={`status-dot ${isLoading ? "status-thinking" : "status-online"}`} />
          <span className="text-xs uppercase tracking-wider text-slate-400">
            {isLoading ? "Processando" : "Online"}
          </span>
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
