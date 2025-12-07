"""
Risk Assessment Constants.

Thresholds, weights, and mappings for risk calculation.
"""

from __future__ import annotations

from ..base_pkg import ActionType

# Risk level thresholds
CRITICAL_THRESHOLD = 0.75  # ≥0.75 → CRITICAL
HIGH_THRESHOLD = 0.50  # ≥0.50 → HIGH (>50% risk is high)
MEDIUM_THRESHOLD = 0.30  # ≥0.30 → MEDIUM
# <0.30 → LOW

# Category weights (must sum to 1.0)
RISK_WEIGHTS = {
    "threat": 0.25,
    "asset": 0.20,
    "business": 0.20,
    "action": 0.15,
    "compliance": 0.10,
    "environmental": 0.10,
}

# Action aggressiveness scores
ACTION_AGGRESSIVENESS = {
    ActionType.SEND_ALERT: 0.0,
    ActionType.CREATE_TICKET: 0.0,
    ActionType.COLLECT_LOGS: 0.1,
    ActionType.COLLECT_FORENSICS: 0.2,
    ActionType.THROTTLE_CONNECTION: 0.3,
    ActionType.SUSPEND_PROCESS: 0.4,
    ActionType.BLOCK_IP: 0.5,
    ActionType.BLOCK_DOMAIN: 0.5,
    ActionType.QUARANTINE_FILE: 0.6,
    ActionType.KILL_PROCESS: 0.6,
    ActionType.ISOLATE_HOST: 0.7,
    ActionType.DISABLE_USER: 0.7,
    ActionType.LOCK_ACCOUNT: 0.7,
    ActionType.DELETE_FILE: 0.8,
    ActionType.RESET_PASSWORD: 0.8,
    ActionType.DELETE_DATA: 0.9,
    ActionType.ENCRYPT_DATA: 0.5,
    ActionType.BACKUP_DATA: 0.2,
}

# Action reversibility scores (0=fully reversible, 1=irreversible)
ACTION_REVERSIBILITY = {
    ActionType.SEND_ALERT: 0.0,
    ActionType.CREATE_TICKET: 0.0,
    ActionType.COLLECT_LOGS: 0.0,
    ActionType.THROTTLE_CONNECTION: 0.1,
    ActionType.BLOCK_IP: 0.2,
    ActionType.BLOCK_DOMAIN: 0.2,
    ActionType.SUSPEND_PROCESS: 0.2,
    ActionType.ISOLATE_HOST: 0.3,
    ActionType.QUARANTINE_FILE: 0.3,
    ActionType.KILL_PROCESS: 0.4,
    ActionType.DISABLE_USER: 0.4,
    ActionType.LOCK_ACCOUNT: 0.4,
    ActionType.RESET_PASSWORD: 0.6,
    ActionType.DELETE_FILE: 0.8,
    ActionType.DELETE_DATA: 0.9,
    ActionType.ENCRYPT_DATA: 0.5,
    ActionType.BACKUP_DATA: 0.1,
}

# Category scoring weights
THREAT_RISK_WEIGHTS = {
    "severity": 0.5,
    "confidence_inverse": 0.3,  # Lower confidence = higher risk
    "novelty": 0.2,
}

ASSET_RISK_WEIGHTS = {
    "criticality": 0.5,
    "data_sensitivity": 0.3,
    "asset_count": 0.2,
}

BUSINESS_RISK_WEIGHTS = {
    "financial_impact": 0.4,
    "operational_impact": 0.3,
    "reputational_impact": 0.3,
}

ACTION_RISK_WEIGHTS = {
    "reversibility": 0.5,
    "aggressiveness": 0.3,
    "scope": 0.2,
}

COMPLIANCE_RISK_WEIGHTS = {
    "compliance_impact": 0.6,
    "privacy_impact": 0.4,
}

ENVIRONMENTAL_RISK_WEIGHTS = {
    "time_of_day": 0.5,
    "operator_availability_inverse": 0.5,  # Low availability = high risk
}

# Criticality mapping
CRITICALITY_SCORES = {
    "low": 0.2,
    "medium": 0.5,
    "high": 0.8,
    "critical": 1.0,
}

# Data sensitivity mapping
SENSITIVITY_SCORES = {
    "public": 0.0,
    "internal": 0.3,
    "confidential": 0.6,
    "restricted": 0.8,
    "top_secret": 1.0,
}

# Operational impact mapping
OPERATIONAL_IMPACT_KEYWORDS = {
    "critical": 1.0,
    "severe": 1.0,
    "high": 0.8,
    "major": 0.8,
    "moderate": 0.5,
    "medium": 0.5,
    "low": 0.3,
    "minor": 0.3,
}

# Scope mapping
SCOPE_SCORES = {
    "global": 1.0,
    "organization": 0.8,
    "department": 0.5,
    "host": 0.2,
    "local": 0.1,
}
