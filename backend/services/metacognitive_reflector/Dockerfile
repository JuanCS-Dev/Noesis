FROM python:3.11-slim

WORKDIR /app

# Install UV
RUN pip install --no-cache-dir uv

# Copy project definition
COPY pyproject.toml .
# Copy source code (needed for pip install .)
COPY . .

# Install dependencies from pyproject.toml
RUN uv pip install --system .

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=5s \
  CMD exit 0

# Run application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

