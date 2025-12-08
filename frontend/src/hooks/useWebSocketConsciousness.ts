"use client";

import { useState, useEffect, useCallback, useRef } from "react";

/**
 * WebSocket event types from the consciousness backend
 */
export type WSEventType =
  | "initial_state"
  | "state_snapshot"
  | "heartbeat"
  | "pong"
  | "esgt_event"
  | "arousal_change";

/**
 * WebSocket event from backend
 */
export interface WSEvent {
  type: WSEventType;
  timestamp?: string;
  arousal?: number;
  events_count?: number;
  esgt_active?: boolean;
  [key: string]: unknown;
}

/**
 * Connection status
 */
export type ConnectionStatus = "disconnected" | "connecting" | "connected" | "reconnecting";

interface UseWebSocketConsciousnessOptions {
  enabled?: boolean;
  wsUrl?: string;
  reconnectIntervalMs?: number;
  maxReconnectAttempts?: number;
  onEvent?: (event: WSEvent) => void;
}

interface UseWebSocketConsciousnessResult {
  status: ConnectionStatus;
  lastEvent: WSEvent | null;
  arousal: number | null;
  esgtActive: boolean;
  eventsCount: number;
  reconnectAttempts: number;
  connect: () => void;
  disconnect: () => void;
  sendPing: () => void;
}

const DEFAULT_WS_URL = "ws://localhost:8001/api/consciousness/ws";
const DEFAULT_RECONNECT_INTERVAL = 3000;
const DEFAULT_MAX_RECONNECT_ATTEMPTS = 10;

/**
 * Hook para conexão WebSocket com o MAXIMUS Consciousness System
 * 
 * Conecta em WS /api/consciousness/ws para streaming real-time de:
 * - state_snapshot: Estado periódico do sistema
 * - arousal_change: Mudanças no nível de arousal
 * - esgt_event: Eventos do protocolo ESGT
 */
export function useWebSocketConsciousness(
  options: UseWebSocketConsciousnessOptions = {}
): UseWebSocketConsciousnessResult {
  const {
    enabled = true,
    wsUrl = DEFAULT_WS_URL,
    reconnectIntervalMs = DEFAULT_RECONNECT_INTERVAL,
    maxReconnectAttempts = DEFAULT_MAX_RECONNECT_ATTEMPTS,
    onEvent,
  } = options;

  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [lastEvent, setLastEvent] = useState<WSEvent | null>(null);
  const [arousal, setArousal] = useState<number | null>(null);
  const [esgtActive, setEsgtActive] = useState(false);
  const [eventsCount, setEventsCount] = useState(0);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isManualDisconnect = useRef(false);

  const cleanup = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
      wsRef.current = null;
    }
  }, []);

  const handleEvent = useCallback(
    (event: WSEvent) => {
      setLastEvent(event);

      // Update state based on event type
      if (event.arousal !== undefined) {
        setArousal(event.arousal);
      }
      if (event.esgt_active !== undefined) {
        setEsgtActive(event.esgt_active);
      }
      if (event.events_count !== undefined) {
        setEventsCount(event.events_count);
      }

      // Call external handler
      onEvent?.(event);
    },
    [onEvent]
  );

  const connect = useCallback(() => {
    if (!enabled) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    cleanup();
    isManualDisconnect.current = false;
    setStatus("connecting");

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        setReconnectAttempts(0);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WSEvent;
          handleEvent(data);
        } catch {
          // Invalid JSON, ignore
        }
      };

      ws.onclose = () => {
        setStatus("disconnected");
        wsRef.current = null;

        // Auto-reconnect with exponential backoff
        if (!isManualDisconnect.current && reconnectAttempts < maxReconnectAttempts) {
          const backoff = Math.min(
            reconnectIntervalMs * Math.pow(1.5, reconnectAttempts),
            30000
          );
          setStatus("reconnecting");
          setReconnectAttempts((prev) => prev + 1);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, backoff);
        }
      };

      ws.onerror = () => {
        // Error handling is done in onclose
      };
    } catch {
      setStatus("disconnected");
    }
  }, [
    enabled,
    wsUrl,
    cleanup,
    handleEvent,
    reconnectAttempts,
    reconnectIntervalMs,
    maxReconnectAttempts,
  ]);

  const disconnect = useCallback(() => {
    isManualDisconnect.current = true;
    cleanup();
    setStatus("disconnected");
    setReconnectAttempts(0);
  }, [cleanup]);

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send("ping");
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      cleanup();
    };
  }, [enabled, connect, cleanup]);

  return {
    status,
    lastEvent,
    arousal,
    esgtActive,
    eventsCount,
    reconnectAttempts,
    connect,
    disconnect,
    sendPing,
  };
}

export default useWebSocketConsciousness;

