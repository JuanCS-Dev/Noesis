"""
Tests for Tribunal MCP Tools
=============================

Scientific tests for Tribunal service integration via MCP tools.

Follows CODE_CONSTITUTION: ≥85% coverage, clear test names.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from tools.tribunal_tools import (
    tribunal_evaluate,
    tribunal_health,
    tribunal_stats,
    TribunalEvaluateRequest,
    TribunalEvaluateResponse,
)
from clients.tribunal_client import TribunalClient


class TestTribunalEvaluateRequest:
    """Test TribunalEvaluateRequest validation."""

    def test_request_with_execution_log_only(self):
        """HYPOTHESIS: Request accepts execution_log alone."""
        request = TribunalEvaluateRequest(execution_log="test log")
        assert request.execution_log == "test log"
        assert request.context is None

    def test_request_with_context(self):
        """HYPOTHESIS: Request accepts optional context."""
        request = TribunalEvaluateRequest(
            execution_log="test log",
            context={"user": "test_user"}
        )
        assert request.context == {"user": "test_user"}

    def test_request_validation_empty_log(self):
        """HYPOTHESIS: Empty execution_log raises ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TribunalEvaluateRequest(execution_log="")

    def test_request_validation_log_too_long(self):
        """HYPOTHESIS: Execution log > 10000 chars raises error."""
        from pydantic import ValidationError
        long_log = "x" * 10001
        with pytest.raises(ValidationError):
            TribunalEvaluateRequest(execution_log=long_log)


class TestTribunalEvaluateResponse:
    """Test TribunalEvaluateResponse parsing."""

    def test_response_parsing_pass(self, mock_tribunal_response):
        """HYPOTHESIS: Response parses PASS decision."""
        response = TribunalEvaluateResponse(**mock_tribunal_response)
        assert response.decision == "PASS"
        assert response.consensus_score == 0.85
        assert response.punishment is None

    def test_response_parsing_with_punishment(self, mock_tribunal_response):
        """HYPOTHESIS: Response parses punishment when present."""
        mock_tribunal_response["decision"] = "FAIL"
        mock_tribunal_response["punishment"] = "retry_required"

        response = TribunalEvaluateResponse(**mock_tribunal_response)
        assert response.decision == "FAIL"
        assert response.punishment == "retry_required"

    def test_response_validation_invalid_decision(self, mock_tribunal_response):
        """HYPOTHESIS: Invalid decision raises ValidationError."""
        from pydantic import ValidationError
        mock_tribunal_response["decision"] = "INVALID"

        with pytest.raises(ValidationError):
            TribunalEvaluateResponse(**mock_tribunal_response)

    def test_response_validation_score_range(self, mock_tribunal_response):
        """HYPOTHESIS: Consensus score must be 0.0-1.0."""
        from pydantic import ValidationError
        mock_tribunal_response["consensus_score"] = 1.5

        with pytest.raises(ValidationError):
            TribunalEvaluateResponse(**mock_tribunal_response)


class TestTribunalEvaluateTool:
    """Test tribunal_evaluate MCP tool."""

    @pytest.mark.asyncio
    async def test_evaluate_success(self, mock_tribunal_response):
        """HYPOTHESIS: Successful evaluation returns verdict."""
        with patch("clients.tribunal_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_tribunal_response
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await tribunal_evaluate(
                execution_log="test log",
                context=None
            )

            assert result["decision"] == "PASS"
            assert result["consensus_score"] == 0.85

    @pytest.mark.asyncio
    async def test_evaluate_with_context(self, mock_tribunal_response):
        """HYPOTHESIS: Context is passed to client."""
        context = {"user": "test_user", "session": "abc123"}

        with patch("clients.tribunal_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_tribunal_response
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await tribunal_evaluate(
                execution_log="test log",
                context=context
            )

            assert result["decision"] == "PASS"
            # Verify context was included in the call
            call_json = mock_http.post.call_args[1]["json"]
            assert call_json["context"] == context


class TestTribunalHealthTool:
    """Test tribunal_health MCP tool."""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """HYPOTHESIS: Health check returns service status."""
        with patch("clients.tribunal_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.get.return_value = {
                "status": "healthy",
                "judges": ["VERITAS", "SOPHIA", "DIKE"],
                "uptime": 3600
            }
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await tribunal_health()

            assert result["status"] == "healthy"
            assert len(result["judges"]) == 3

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """HYPOTHESIS: Health check detects unhealthy service."""
        with patch("clients.tribunal_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.get.return_value = {
                "status": "unhealthy",
                "error": "Database connection failed"
            }
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await tribunal_health()

            assert result["status"] == "unhealthy"
            assert "error" in result


class TestTribunalStatsTool:
    """Test tribunal_stats MCP tool."""

    @pytest.mark.asyncio
    async def test_stats_success(self):
        """HYPOTHESIS: Stats returns tribunal metrics."""
        with patch("clients.tribunal_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.get.return_value = {
                "total_evaluations": 1523,
                "decisions": {"PASS": 1245, "REVIEW": 200, "FAIL": 78},
                "avg_consensus_score": 0.82
            }
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await tribunal_stats()

            assert result["total_evaluations"] == 1523
            assert result["decisions"]["PASS"] == 1245

    @pytest.mark.asyncio
    async def test_stats_empty(self):
        """HYPOTHESIS: Stats returns zeros for new tribunal."""
        with patch("clients.tribunal_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.get.return_value = {
                "total_evaluations": 0,
                "decisions": {},
                "avg_consensus_score": 0.0
            }
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await tribunal_stats()

            assert result["total_evaluations"] == 0


class TestTribunalToolsIntegration:
    """Test integration scenarios."""

    @pytest.mark.asyncio
    async def test_evaluate_then_check_health(self, mock_tribunal_response):
        """HYPOTHESIS: Can evaluate then check health."""
        with patch("clients.tribunal_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_tribunal_response
            mock_http.get.return_value = {"status": "healthy"}
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            # Evaluate
            verdict = await tribunal_evaluate("test log")
            assert verdict["decision"] == "PASS"

            # Check health
            health = await tribunal_health()
            assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_evaluate_then_check_stats(self, mock_tribunal_response):
        """HYPOTHESIS: Can evaluate then check stats."""
        with patch("clients.tribunal_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_tribunal_response
            mock_http.get.return_value = {"total_evaluations": 1}
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            # Evaluate
            verdict = await tribunal_evaluate("test log")
            assert verdict["decision"] == "PASS"

            # Check stats
            stats = await tribunal_stats()
            assert stats["total_evaluations"] >= 1


class TestTribunalToolsErrorHandling:
    """Test error handling edge cases."""

    @pytest.mark.asyncio
    async def test_malformed_response_from_tribunal(self):
        """HYPOTHESIS: Malformed response raises appropriate error."""
        from pydantic import ValidationError
        with patch("clients.tribunal_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            # Missing required fields (verdicts and trace_id)
            mock_http.post.return_value = {"decision": "PASS", "consensus_score": 0.85}
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            with pytest.raises(ValidationError):
                await tribunal_evaluate("test log")

    @pytest.mark.asyncio
    async def test_network_error_propagation(self):
        """HYPOTHESIS: Network errors propagate correctly."""
        with patch("clients.tribunal_client.BaseHTTPClient") as MockHTTP:
            import httpx
            mock_http = AsyncMock()
            mock_http.post.side_effect = httpx.ConnectError("Connection refused")
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            with pytest.raises(httpx.ConnectError):
                await tribunal_evaluate("test log")

    @pytest.mark.asyncio
    async def test_trace_id_propagation(self, mock_tribunal_response):
        """HYPOTHESIS: Trace ID is propagated through calls."""
        trace_id = "test-trace-abc123"
        mock_tribunal_response["trace_id"] = trace_id

        with patch("clients.tribunal_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_tribunal_response
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await tribunal_evaluate("test log")

            assert result["trace_id"] == trace_id
