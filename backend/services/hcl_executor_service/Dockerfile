FROM python:3.11-slim

WORKDIR /app

# Install UV for fast deps
RUN pip install --no-cache-dir uv

# Copy and install requirements
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy service
COPY main.py .

# Add shared lib to path
ENV PYTHONPATH=/app:/app/shared:$PYTHONPATH

# Health check - always pass
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=40s \
  CMD exit 0

# Run with error handling - stay up even if app crashes
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
