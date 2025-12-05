"""
Honeytoken Tables for PostgreSQL Honeypot.

Honeytoken table creation and audit triggers.
"""

from __future__ import annotations

from typing import Any, Dict, List


class HoneytokenMixin:
    """Mixin providing honeytoken table generation."""

    honeytokens_planted: List[Dict[str, Any]]

    def _build_honeytoken_tables(self) -> str:
        """Build tables with honeytokens."""
        sql = """
-- Honeytokens table (HIGHLY SENSITIVE)
CREATE TABLE IF NOT EXISTS api_credentials (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    api_secret VARCHAR(255) NOT NULL,
    environment VARCHAR(20) DEFAULT 'production',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    notes TEXT
);

-- Plant honeytokens
INSERT INTO api_credentials (service_name, api_key, api_secret, environment, notes)
VALUES
    ('AWS Production', 'AKIAIOSFODNN7EXAMPLE', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY', 'production', 'Main AWS account - DO NOT SHARE'),
    ('Stripe Payment Gateway', 'sk_live_51HnToken12345Example', 'whsec_HoneytokenWebhookSecret123', 'production', 'Production payment processing'),
    ('SendGrid Email', 'SG.HoneytokenExampleSendGridKey.1234567890abcdef', NULL, 'production', 'Email service API key'),
    ('GitHub Deploy', 'ghp_HoneytokenGitHubPersonalAccessToken123456', NULL, 'production', 'CI/CD deployment key'),
    ('Database Backup', 'backup_user:Sup3rS3cr3tBackupP@ssw0rd!', NULL, 'production', 'Automated backup credentials');

-- SSH Keys table
CREATE TABLE IF NOT EXISTS ssh_keys (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL,
    public_key TEXT NOT NULL,
    private_key TEXT NOT NULL,
    passphrase VARCHAR(255),
    server VARCHAR(255),
    purpose TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plant SSH honeytokens
INSERT INTO ssh_keys (key_name, public_key, private_key, server, purpose)
VALUES (
    'production-server-key',
    'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDHoneytokenPublicKey root@prod',
    '-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAHoneytokenPrivateKeyContent
[... truncated for brevity ...]
-----END RSA PRIVATE KEY-----',
    'prod-app-01.internal.company.com',
    'Production application server access'
);

-- Internal endpoints table
CREATE TABLE IF NOT EXISTS internal_endpoints (
    id SERIAL PRIMARY KEY,
    endpoint_name VARCHAR(100),
    url VARCHAR(500),
    api_key VARCHAR(255),
    description TEXT
);

INSERT INTO internal_endpoints (endpoint_name, url, api_key, description)
VALUES
    ('Internal Admin API', 'https://admin.internal.company.com/api/v1', 'admin_token_honeytoken_12345', 'Internal admin dashboard API'),
    ('Metrics Collector', 'https://metrics.internal.company.com', 'metrics_key_honeytoken_67890', 'Application metrics endpoint'),
    ('CI/CD Webhook', 'https://deploy.internal.company.com/webhook', 'webhook_secret_honeytoken_abcdef', 'Deployment automation');
"""

        # Track planted honeytokens
        self.honeytokens_planted = [
            {"type": "aws_credentials", "identifier": "AKIAIOSFODNN7EXAMPLE"},
            {"type": "stripe_key", "identifier": "sk_live_51HnToken12345Example"},
            {"type": "ssh_private_key", "identifier": "production-server-key"},
            {"type": "github_pat", "identifier": "ghp_HoneytokenGitHub"},
            {"type": "internal_api", "identifier": "admin_token_honeytoken"},
        ]

        return sql

    def _build_audit_triggers(self) -> str:
        """Build audit triggers to detect suspicious access."""
        return """
-- Audit log table
CREATE TABLE IF NOT EXISTS query_audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(100),
    database_name VARCHAR(100),
    query_text TEXT,
    rows_affected INTEGER,
    execution_time_ms INTEGER,
    client_ip VARCHAR(50),
    suspicious BOOLEAN DEFAULT FALSE,
    alert_triggered BOOLEAN DEFAULT FALSE
);

-- Function to log sensitive table access
CREATE OR REPLACE FUNCTION log_sensitive_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO query_audit_log (username, database_name, query_text, suspicious, alert_triggered)
    VALUES (
        current_user,
        current_database(),
        current_query(),
        TRUE,  -- Mark as suspicious
        TRUE   -- Trigger alert
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for sensitive tables
CREATE TRIGGER audit_api_credentials_access
    AFTER SELECT ON api_credentials
    FOR EACH STATEMENT
    EXECUTE FUNCTION log_sensitive_access();

CREATE TRIGGER audit_ssh_keys_access
    AFTER SELECT ON ssh_keys
    FOR EACH STATEMENT
    EXECUTE FUNCTION log_sensitive_access();

-- Grant permissions to honeypot user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO backup_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO backup_user;
"""
