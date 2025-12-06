# API Gateway Service

Minimalist gateway to route external requests to internal services.

## Quick Start

```bash
# Run service
python -m backend.services.api_gateway.main
```

## Architecture

Acts as a reverse proxy. Handles authentication and rate limiting.

## API

- Routes requests to `/api/v1/{service_name}`.

## Configuration

- `SERVICES_MAP`: Mapping of service names to internal URLs.
