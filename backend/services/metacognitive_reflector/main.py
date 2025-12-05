"""
Metacognitive Reflector: Service Entry Point
============================================

Entry point for running the Metacognitive Reflector service.
"""

from __future__ import annotations

import uvicorn
from .main_v2 import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8101)
