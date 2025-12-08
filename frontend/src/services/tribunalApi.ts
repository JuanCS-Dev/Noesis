/**
 * Tribunal API Service
 * ====================
 * 
 * Client for the Metacognitive Reflector tribunal service.
 * Provides access to the Three Judges system (Veritas, Sophia, Dike).
 */

const TRIBUNAL_BASE_URL = "http://localhost:8002/api/reflector";

/**
 * Judge verdict from individual judge
 */
export interface JudgeVerdict {
  pillar: string;
  passed: boolean;
  confidence: number;
  reasoning: string;
  suggestions: string[];
}

/**
 * Vote breakdown for a judge
 */
export interface VoteBreakdown {
  judge_name: string;
  pillar: string;
  vote: number;
  weight: number;
  weighted_vote: number;
  abstained: boolean;
}

/**
 * Full tribunal verdict response
 */
export interface TribunalVerdict {
  decision: "PASS" | "REVIEW" | "FAIL";
  consensus_score: number;
  individual_verdicts: {
    [judgeName: string]: JudgeVerdict;
  };
  vote_breakdown: VoteBreakdown[];
  reasoning: string;
  offense_level: string;
  requires_human_review: boolean;
  punishment_recommendation: string | null;
  abstention_count: number;
  execution_time_ms: number;
}

/**
 * Tribunal health status
 */
export interface TribunalHealth {
  healthy: boolean;
  tribunal: {
    status: string;
    judges: {
      veritas: { status: string; last_response_ms?: number };
      sophia: { status: string; last_response_ms?: number };
      dike: { status: string; last_response_ms?: number };
    };
    arbiter: { status: string };
  };
  executor: {
    status: string;
    active_punishments: number;
  };
  memory: {
    status: string;
    backend: string;
  };
}

/**
 * Agent punishment status
 */
export interface AgentStatus {
  agent_id: string;
  active: boolean;
  status: string;
  punishment_type: string | null;
  started_at: string | null;
  details: Record<string, unknown>;
}

/**
 * Service health check
 */
export interface ServiceHealth {
  status: string;
  service: string;
}

/**
 * Check if tribunal service is online
 */
export async function checkTribunalHealth(): Promise<ServiceHealth | null> {
  try {
    const response = await fetch(`${TRIBUNAL_BASE_URL}/health`, {
      method: "GET",
      headers: { Accept: "application/json" },
    });

    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

/**
 * Get detailed tribunal health including judge status
 */
export async function getTribunalDetailedHealth(): Promise<TribunalHealth | null> {
  try {
    const response = await fetch(`${TRIBUNAL_BASE_URL}/health/detailed`, {
      method: "GET",
      headers: { Accept: "application/json" },
    });

    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

/**
 * Get agent punishment status
 */
export async function getAgentStatus(agentId: string): Promise<AgentStatus | null> {
  try {
    const response = await fetch(`${TRIBUNAL_BASE_URL}/agent/${agentId}/status`, {
      method: "GET",
      headers: { Accept: "application/json" },
    });

    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

/**
 * Judge display configuration
 */
export interface JudgeConfig {
  id: string;
  name: string;
  pillar: string;
  spiritualSymbol: string;
  description: string;
  color: {
    primary: string;
    glow: string;
    bg: string;
    border: string;
  };
  icon: "shield" | "brain" | "scale";
}

/**
 * Static configuration for the Three Judges
 */
export const JUDGES_CONFIG: JudgeConfig[] = [
  {
    id: "veritas",
    name: "VERITAS",
    pillar: "Truth",
    spiritualSymbol: "✝",
    description: "Jesus - O Caminho, a Verdade, a Vida",
    color: {
      primary: "text-cyan-400",
      glow: "shadow-cyan-400/50",
      bg: "bg-cyan-900/20",
      border: "border-cyan-500/30",
    },
    icon: "shield",
  },
  {
    id: "sophia",
    name: "SOPHIA",
    pillar: "Wisdom",
    spiritualSymbol: "☀",
    description: "Espírito Santo - Sabedoria Divina",
    color: {
      primary: "text-purple-400",
      glow: "shadow-purple-400/50",
      bg: "bg-purple-900/20",
      border: "border-purple-500/30",
    },
    icon: "brain",
  },
  {
    id: "dike",
    name: "DIKĒ",
    pillar: "Justice",
    spiritualSymbol: "⚖",
    description: "Deus Pai - Justiça Perfeita",
    color: {
      primary: "text-amber-400",
      glow: "shadow-amber-400/50",
      bg: "bg-amber-900/20",
      border: "border-amber-500/30",
    },
    icon: "scale",
  },
];

/**
 * Get judge config by ID
 */
export function getJudgeConfig(judgeId: string): JudgeConfig | undefined {
  return JUDGES_CONFIG.find(
    (j) => j.id.toLowerCase() === judgeId.toLowerCase()
  );
}

export default {
  checkTribunalHealth,
  getTribunalDetailedHealth,
  getAgentStatus,
  JUDGES_CONFIG,
  getJudgeConfig,
};

