"""
Metacognitive Reflector: Service Entry Point
============================================

FastAPI application for tribunal evaluation and metacognitive analysis.
"""

from __future__ import annotations

from fastapi import FastAPI

from metacognitive_reflector.api.routes import router


app = FastAPI(
    title="Metacognitive Reflector",
    description="MAXIMUS Tribunal evaluation and metacognitive analysis",
    version="3.0.0",
)

# Include the API router
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8101)
