/**
 * Hooks Index
 * ===========
 * 
 * Central export for all custom hooks.
 */

export {
  useConsciousnessMetrics,
  deriveMetricsForUI,
  type ReactiveFabricMetrics,
  type SafetyStatus,
} from "./useConsciousnessMetrics";

export {
  useWebSocketConsciousness,
  type WSEventType,
  type WSEvent,
  type ConnectionStatus,
} from "./useWebSocketConsciousness";

