FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY main.py .

ENV PYTHONPATH=/app:/app/shared:$PYTHONPATH

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=40s CMD exit 0

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
