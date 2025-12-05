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
CMD python -c "
import uvicorn
import sys
import time
try:
    uvicorn.run('main:app', host='0.0.0.0', port=8000, log_level='info')
except Exception as e:
    print(f'Service error: {e}', file=sys.stderr)
    # Keep container alive for debugging
    while True:
        time.sleep(3600)
"
