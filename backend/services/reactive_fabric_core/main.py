from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import os

app = FastAPI(title=os.getenv("SERVICE_NAME", "service"))

@app.get("/health")
async def health():
    return {"status": "healthy", "service": os.getenv("SERVICE_NAME", "unknown")}

@app.get("/metrics")
async def metrics():
    return PlainTextResponse("# No metrics yet\n")

@app.get("/")
async def root():
    return {"message": "Service operational"}
