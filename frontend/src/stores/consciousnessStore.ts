"use client";

import { create } from "zustand";

// ESGT Phase types matching backend
export type ESGTPhase =
  | "idle"
  | "prepare"
  | "synchronize"
  | "broadcast"
  | "sustain"
  | "dissolve"
  | "complete"
  | "failed";

// WebSocket connection status
export type WSConnectionStatus = "disconnected" | "connecting" | "connected" | "reconnecting";

// Stream event types from SSE
export interface StreamEvent {
  type: "start" | "phase" | "coherence" | "token" | "complete" | "error";
  data: Record<string, unknown>;
  timestamp: string;
}

// WebSocket event from backend
export interface WSEvent {
  type: string;
  timestamp?: string;
  arousal?: number;
  events_count?: number;
  esgt_active?: boolean;
  [key: string]: unknown;
}

// Consciousness state interface
interface ConsciousnessState {
  // SSE Connection state
  isConnected: boolean;
  isStreaming: boolean;

  // WebSocket state
  wsStatus: WSConnectionStatus;
  wsArousal: number | null;
  wsEsgtActive: boolean;
  wsEventsCount: number;

  // ESGT state (real-time from backend)
  currentPhase: ESGTPhase;
  coherence: number;
  targetCoherence: number;

  // Streaming text
  tokens: string[];
  fullResponse: string;

  // Event history
  events: StreamEvent[];

  // Error handling
  error: string | null;

  // SSE Actions
  startStream: (content: string, depth?: number) => void;
  stopStream: () => void;
  updatePhase: (phase: ESGTPhase) => void;
  updateCoherence: (value: number) => void;
  addToken: (token: string) => void;
  setError: (error: string | null) => void;
  reset: () => void;

  // WebSocket Actions
  setWSStatus: (status: WSConnectionStatus) => void;
  handleWSEvent: (event: WSEvent) => void;
  setWSArousal: (arousal: number | null) => void;
  setWSEsgtActive: (active: boolean) => void;
}

// EventSource instance (module-level for cleanup)
let eventSource: EventSource | null = null;

export const useConsciousnessStore = create<ConsciousnessState>((set, get) => ({
  // Initial SSE state
  isConnected: false,
  isStreaming: false,
  currentPhase: "idle",
  coherence: 0,
  targetCoherence: 0.70,
  tokens: [],
  fullResponse: "",
  events: [],
  error: null,

  // Initial WebSocket state
  wsStatus: "disconnected",
  wsArousal: null,
  wsEsgtActive: false,
  wsEventsCount: 0,

  // Start streaming from backend
  startStream: (content: string, depth: number = 3) => {
    // Close existing connection
    if (eventSource) {
      eventSource.close();
    }

    // Reset state for new stream
    set({
      isStreaming: true,
      isConnected: false,
      currentPhase: "prepare",
      coherence: 0,
      tokens: [],
      fullResponse: "",
      events: [],
      error: null,
      targetCoherence: 0.70 + (depth * 0.05),
    });

    // Create SSE connection
    const url = `http://localhost:8001/api/consciousness/stream/process?content=${encodeURIComponent(content)}&depth=${depth}`;
    eventSource = new EventSource(url);

    eventSource.onopen = () => {
      set({ isConnected: true });
      console.log("[Consciousness] SSE connected");
    };

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        const event: StreamEvent = {
          type: data.type,
          data: data,
          timestamp: new Date().toISOString(),
        };

        // Add to event history
        set((state) => ({ events: [...state.events, event] }));

        // Handle different event types
        switch (data.type) {
          case "start":
            set({ currentPhase: "prepare" });
            break;

          case "phase":
            set({ currentPhase: data.phase as ESGTPhase });
            break;

          case "coherence":
            set({ coherence: data.value });
            break;

          case "token":
            set((state) => ({
              tokens: [...state.tokens, data.token],
              fullResponse: state.fullResponse + data.token,
            }));
            break;

          case "complete":
            set({
              isStreaming: false,
              currentPhase: "complete",
            });
            eventSource?.close();
            break;

          case "error":
            set({
              error: data.message || "Unknown error",
              currentPhase: "failed",
              isStreaming: false,
            });
            eventSource?.close();
            break;
        }
      } catch (err) {
        console.error("[Consciousness] Parse error:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("[Consciousness] SSE error:", err);
      set({
        isConnected: false,
        isStreaming: false,
        error: "Connection lost",
        currentPhase: "failed",
      });
      eventSource?.close();
    };
  },

  // Stop streaming
  stopStream: () => {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
    set({
      isStreaming: false,
      isConnected: false,
      currentPhase: "idle",
    });
  },

  // Manual state updates (for testing/fallback)
  updatePhase: (phase: ESGTPhase) => set({ currentPhase: phase }),
  updateCoherence: (value: number) => set({ coherence: value }),
  addToken: (token: string) =>
    set((state) => ({
      tokens: [...state.tokens, token],
      fullResponse: state.fullResponse + token,
    })),
  setError: (error: string | null) => set({ error }),

  // Reset to initial state
  reset: () => {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
    set({
      isConnected: false,
      isStreaming: false,
      currentPhase: "idle",
      coherence: 0,
      targetCoherence: 0.70,
      tokens: [],
      fullResponse: "",
      events: [],
      error: null,
    });
  },

  // =========================================================================
  // WebSocket Actions for Real-Time State
  // =========================================================================

  setWSStatus: (status: WSConnectionStatus) => set({ wsStatus: status }),

  handleWSEvent: (event: WSEvent) => {
    const updates: Partial<ConsciousnessState> = {};

    // Update arousal from WS event
    if (event.arousal !== undefined) {
      updates.wsArousal = event.arousal;
    }

    // Update ESGT active status
    if (event.esgt_active !== undefined) {
      updates.wsEsgtActive = event.esgt_active;
    }

    // Update events count
    if (event.events_count !== undefined) {
      updates.wsEventsCount = event.events_count;
    }

    // Handle specific event types
    switch (event.type) {
      case "initial_state":
        // Full state on connection
        if (event.arousal !== undefined) updates.wsArousal = event.arousal;
        if (event.esgt_active !== undefined) updates.wsEsgtActive = event.esgt_active;
        if (event.events_count !== undefined) updates.wsEventsCount = event.events_count;
        break;

      case "state_snapshot":
        // Periodic state update - already handled above
        break;

      case "arousal_change":
        // Specific arousal update
        if (event.arousal !== undefined) updates.wsArousal = event.arousal;
        break;

      case "esgt_event":
        // ESGT event notification
        if (event.phase !== undefined) {
          updates.currentPhase = event.phase as ESGTPhase;
        }
        break;
    }

    if (Object.keys(updates).length > 0) {
      set(updates);
    }
  },

  setWSArousal: (arousal: number | null) => set({ wsArousal: arousal }),

  setWSEsgtActive: (active: boolean) => set({ wsEsgtActive: active }),
}));
