"""
Episodic Memory: Service Entry Point
====================================

Entry point for running the Episodic Memory service.
"""

from __future__ import annotations

import uvicorn
from api.routes import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8102)
