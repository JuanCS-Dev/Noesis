FROM python:3.11-slim

WORKDIR /app

# Install UV for fast deps
RUN pip install --no-cache-dir uv

# Copy and install requirements
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy service
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=5s \
  CMD exit 0

# Run application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

