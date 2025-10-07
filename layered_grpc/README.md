# Layered Architecture with gRPC

## Architecture Overview

This is a 3-tier layered architecture with 5 nodes:

1. **API Gateway** (Layer 1) - HTTP → gRPC converter
2. **Business Logic** (Layer 2) - Validation & business rules
3. **Data Service** (Layer 3) - Database operations
4. **Redis Master** (Layer 4) - Primary storage
5. **Redis Replica** (Layer 5) - Backup storage

## Quick Start

```bash
# Build all containers
docker-compose -f docker-compose.layered.yaml build

# Start all services
docker-compose -f docker-compose.layered.yaml up -d

# Check status
docker-compose -f docker-compose.layered.yaml ps

# View logs
docker-compose -f docker-compose.layered.yaml logs -f
```

## Testing

```bash
# Health check
curl http://localhost:8080/healthz

# Create short URL
curl -X POST http://localhost:8080/shorten \
  -H "Content-Type: application/json" \
  -d '{"long_url":"https://www.google.com","ttl_sec":3600,"max_clicks":10}'

# Test redirect
curl -L http://localhost:8080/{code}

# Get analytics
curl http://localhost:8080/analytics/top?limit=5
```

## Stop Services

```bash
docker-compose -f docker-compose.layered.yaml down
```
