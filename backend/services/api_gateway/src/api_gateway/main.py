"""
API Gateway: Service Entry Point
================================

Entry point for running the API Gateway service.
"""

import uvicorn
from api_gateway.api.routes import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
