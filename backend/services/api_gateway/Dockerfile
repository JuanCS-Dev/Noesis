FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency installation
RUN pip install --no-cache-dir uv

# Copy package files
COPY pyproject.toml .
COPY src/ src/

# Install package in editable mode
RUN uv pip install --system -e .

# Set environment
ENV PYTHONPATH=/app/src:$PYTHONPATH
ENV DOCKER_ENV=true

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run using package path
CMD ["python", "-m", "uvicorn", "api_gateway.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
