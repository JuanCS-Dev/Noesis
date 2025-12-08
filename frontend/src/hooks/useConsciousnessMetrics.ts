"use client";

import { useState, useEffect, useCallback, useRef } from "react";

/**
 * Reactive Fabric Metrics from /api/consciousness/reactive-fabric/metrics
 */
export interface ReactiveFabricMetrics {
  timestamp: string;
  tig: {
    node_count: number;
    edge_count: number;
    avg_latency_us: number;
    coherence: number;
  };
  esgt: {
    event_count: number;
    success_rate: number;
    frequency_hz: number;
    avg_coherence: number;
  };
  arousal: {
    level: number;
    classification: string;
    stress: number;
    need: number;
  };
  pfc: {
    signals_processed: number;
    actions_generated: number;
    approval_rate: number;
  };
  tom: {
    total_agents: number;
    total_beliefs: number;
    cache_hit_rate: number;
  };
  safety: {
    violations: number;
    kill_switch_active: boolean;
  };
  health_score: number;
  collection_duration_ms: number;
  errors: string[];
}

/**
 * Safety Status from /api/consciousness/safety/status
 */
export interface SafetyStatus {
  protocol_active: boolean;
  safety_level: string;
  violations_count: number;
  last_violation: string | null;
  kill_switch_available: boolean;
}

interface UseConsciousnessMetricsOptions {
  pollingIntervalMs?: number;
  enabled?: boolean;
  baseUrl?: string;
  retryAttempts?: number;
  retryDelayMs?: number;
}

interface UseConsciousnessMetricsResult {
  metrics: ReactiveFabricMetrics | null;
  safetyStatus: SafetyStatus | null;
  isLoading: boolean;
  error: string | null;
  isConnected: boolean;
  lastUpdated: Date | null;
  connectionAttempts: number;
  refetch: () => Promise<void>;
}

const DEFAULT_BASE_URL = "http://localhost:8001/api/consciousness";
const DEFAULT_POLLING_INTERVAL = 5000; // 5 seconds
const DEFAULT_RETRY_ATTEMPTS = 3;
const DEFAULT_RETRY_DELAY = 1000; // 1 second

/**
 * Hook para polling de métricas do MAXIMUS Consciousness System
 * 
 * Endpoints consumidos:
 * - GET /api/consciousness/reactive-fabric/metrics
 * - GET /api/consciousness/safety/status
 */
export function useConsciousnessMetrics(
  options: UseConsciousnessMetricsOptions = {}
): UseConsciousnessMetricsResult {
  const {
    pollingIntervalMs = DEFAULT_POLLING_INTERVAL,
    enabled = true,
    baseUrl = DEFAULT_BASE_URL,
    retryAttempts = DEFAULT_RETRY_ATTEMPTS,
    retryDelayMs = DEFAULT_RETRY_DELAY,
  } = options;

  const [metrics, setMetrics] = useState<ReactiveFabricMetrics | null>(null);
  const [safetyStatus, setSafetyStatus] = useState<SafetyStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [connectionAttempts, setConnectionAttempts] = useState(0);

  const abortControllerRef = useRef<AbortController | null>(null);
  const retryCountRef = useRef(0);

  /**
   * Validate metrics data structure to prevent crashes
   */
  const validateMetrics = (data: unknown): data is ReactiveFabricMetrics => {
    if (!data || typeof data !== "object") return false;
    const d = data as Record<string, unknown>;
    return (
      typeof d.health_score === "number" &&
      d.tig !== undefined &&
      d.arousal !== undefined &&
      d.safety !== undefined
    );
  };

  /**
   * Fetch with retry logic
   */
  const fetchWithRetry = useCallback(
    async (url: string, signal: AbortSignal): Promise<Response | null> => {
      for (let attempt = 0; attempt <= retryAttempts; attempt++) {
        try {
          const response = await fetch(url, {
            signal,
            headers: { Accept: "application/json" },
          });
          if (response.ok) {
            retryCountRef.current = 0;
            return response;
          }
          // Non-retryable HTTP error
          if (response.status >= 400 && response.status < 500) {
            return response;
          }
        } catch (err) {
          if (err instanceof Error && err.name === "AbortError") {
            throw err; // Don't retry aborted requests
          }
          // Retry on network errors
          if (attempt < retryAttempts) {
            await new Promise((resolve) =>
              setTimeout(resolve, retryDelayMs * Math.pow(2, attempt))
            );
          }
        }
      }
      return null;
    },
    [retryAttempts, retryDelayMs]
  );

  const fetchMetrics = useCallback(async () => {
    if (!enabled) return;

    // Cancel any pending request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    setConnectionAttempts((prev) => prev + 1);

    try {
      // Fetch both endpoints in parallel with retry
      const [metricsRes, safetyRes] = await Promise.allSettled([
        fetchWithRetry(
          `${baseUrl}/reactive-fabric/metrics`,
          abortControllerRef.current.signal
        ),
        fetchWithRetry(
          `${baseUrl}/safety/status`,
          abortControllerRef.current.signal
        ),
      ]);

      // Process metrics response
      if (metricsRes.status === "fulfilled" && metricsRes.value?.ok) {
        try {
          const data = await metricsRes.value.json();
          if (validateMetrics(data)) {
            setMetrics(data);
            setIsConnected(true);
            setError(null);
          } else {
            console.warn("[Metrics] Invalid data structure received");
            setError("Invalid metrics data");
          }
        } catch (parseErr) {
          console.warn("[Metrics] JSON parse error:", parseErr);
          setError("Failed to parse metrics");
        }
      } else if (metricsRes.status === "rejected") {
        // Network error - system offline
        if (metricsRes.reason?.name !== "AbortError") {
          setIsConnected(false);
          setError("Consciousness system offline");
        }
      } else if (metricsRes.status === "fulfilled" && !metricsRes.value) {
        // All retries failed
        setIsConnected(false);
        setError("Connection failed after retries");
      }

      // Process safety response (non-critical)
      if (safetyRes.status === "fulfilled" && safetyRes.value?.ok) {
        try {
          const data = await safetyRes.value.json();
          setSafetyStatus(data);
        } catch {
          // Non-critical, ignore parse errors
        }
      }

      setLastUpdated(new Date());
    } catch (err) {
      if (err instanceof Error && err.name !== "AbortError") {
        setError(err.message);
        setIsConnected(false);
      }
    } finally {
      setIsLoading(false);
    }
  }, [baseUrl, enabled, fetchWithRetry]);

  // Initial fetch and polling
  useEffect(() => {
    if (!enabled) {
      setIsLoading(false);
      return;
    }

    // Initial fetch
    fetchMetrics();

    // Setup polling
    const intervalId = setInterval(fetchMetrics, pollingIntervalMs);

    return () => {
      clearInterval(intervalId);
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [enabled, pollingIntervalMs, fetchMetrics]);

  return {
    metrics,
    safetyStatus,
    isLoading,
    error,
    isConnected,
    lastUpdated,
    connectionAttempts,
    refetch: fetchMetrics,
  };
}

/**
 * Valores derivados úteis para UI - com proteção contra dados parciais
 */
export function deriveMetricsForUI(metrics: ReactiveFabricMetrics | null) {
  // Default fallback values
  const defaults = {
    integrityPercent: 0,
    neuronCount: 0,
    coherencePercent: 0,
    arousalLevel: "UNKNOWN",
    safetyViolations: 0,
    isHealthy: false,
  };

  if (!metrics) {
    return defaults;
  }

  // Safe extraction with fallbacks
  try {
    return {
      integrityPercent: Math.round((metrics.health_score ?? 0) * 100),
      neuronCount: metrics.tig?.node_count ?? 0,
      coherencePercent: Math.round((metrics.tig?.coherence ?? 0) * 100),
      arousalLevel: (metrics.arousal?.classification ?? "UNKNOWN").toUpperCase(),
      safetyViolations: metrics.safety?.violations ?? 0,
      isHealthy: 
        (metrics.health_score ?? 0) >= 0.8 && 
        !(metrics.safety?.kill_switch_active ?? false),
    };
  } catch (err) {
    console.warn("[deriveMetricsForUI] Error processing metrics:", err);
    return defaults;
  }
}

export default useConsciousnessMetrics;

