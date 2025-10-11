# URL Shortener - Distributed Systems Project

A distributed URL shortener system implementing two different architectures: **Microservices (HTTP/REST)** and **Layered (gRPC)**.

---

## 🎯 What Does It Do?

Converts long URLs into short codes, just like bit.ly:
- `https://www.example.com/very/long/path` → `http://localhost:8080/abc123`
- Tracks click analytics
- Supports link expiration (time-based and click-based)
- Rate limiting to prevent abuse

---

## 🏗️ Two Architectures

### Architecture 1: Microservices (Port 8080)
- **5 Services**: API Gateway, Redirect, Analytics, Rate Limit, Redis
- **Communication**: HTTP/REST with JSON
- **Good for**: Independent scaling, loose coupling

### Architecture 2: Layered (Port 8081)
- **5 Nodes**: API Gateway, Business Logic, Data Service, Redis Master, Redis Replica
- **Communication**: gRPC (binary protocol)
- **Good for**: Type safety, performance, strict contracts

---

## 📁 Project Structure

```
CSE-5306-DS-PA2-URLShortener/
├── microservices_http/              # Microservices implementation
│   ├── api_gateway/                 # Entry point (Port 8080)
│   ├── redirect_service/            # URL resolution
│   ├── analytics_service/           # Click tracking
│   └── ratelimit_service/           # Request limiting
│
├── layered_simple/                  # Layered implementation
│   ├── src/
│   │   ├── proto/                   # gRPC definitions
│   │   ├── api_gateway/             # HTTP → gRPC (Port 8081)
│   │   ├── business_logic/          # Core logic
│   │   └── data_service/            # Database operations
│
├── common/                          # Shared libraries
│   └── lib/
│       ├── codegen.py               # Short code generator
│       ├── rate_limit.py            # Models & rate limiting
│       └── ttl.py                   # Time-to-live utilities
│
├── persistence/                     # Redis operations
│   ├── redis_client.py              # Redis connection
│   └── repositories.py              # Data access layer
│
└── deploy/
    ├── compose/                     # Docker Compose files
    │   ├── docker-compose.micro.yaml
    │   └── docker-compose.layered.yaml
    └── docker/                      # Dockerfiles
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- `grpcurl` (for layered architecture testing)
  ```bash
  brew install grpcurl  # macOS
  ```

### Start Both Architectures

```bash

# Start Microservices (Port 8080)
docker-compose -f deploy/compose/docker-compose.micro.yaml up -d

# Start Layered (Port 8081)
docker-compose -p layered -f deploy/compose/docker-compose.layered.yaml up -d
```

### Check Status

```bash
# Microservices
docker-compose -f docker-compose.micro.yaml ps

# Layered
docker-compose -p layered -f docker-compose.layered.yaml ps

# Health checks
curl http://localhost:8080/healthz
curl http://localhost:8081/healthz
```

### Stop Services

```bash
# Stop Microservices
docker-compose -f docker-compose.micro.yaml down

# Stop Layered
docker-compose -p layered -f docker-compose.layered.yaml down
```

---

## 🧪 Testing Commands

### Microservices Architecture (HTTP/REST - Port 8080)

#### Create Short URL
```bash
curl -X POST http://localhost:8080/shorten \
  -H "Content-Type: application/json" \
  -d '{"long_url":"https://www.google.com","ttl_sec":3600,"max_clicks":10}'
```

**Response:**
```json
{"code":"Vy6UJ4i","short_url":"http://localhost:8080/Vy6UJ4i"}
```

#### Get Main URL (Follow Redirect)
```bash
curl -L http://localhost:8080/Vy6UJ4i
```

#### Check URL Without Counting Click (HEAD)
```bash
curl -I http://localhost:8080/Vy6UJ4i
```

#### Get Top Links Analytics
```bash
curl http://localhost:8080/analytics/top?limit=5
```

---

### Layered Architecture (gRPC - Port 8081)

#### Create Short URL
```bash
grpcurl -plaintext \
  -proto layered_simple/src/proto/urlshortener.proto \
  -import-path layered_simple/src/proto \
  -d '{"long_url": "https://www.google.com", "client_ip": "127.0.0.1"}' \
  localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL
```

#### Resolve URL (Count Click)
```bash
grpcurl -plaintext \
  -proto layered_simple/src/proto/urlshortener.proto \
  -import-path layered_simple/src/proto \
  -d '{"code": "YOUR_CODE", "count_click": true, "client_ip": "127.0.0.1"}' \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL
```

#### Resolve URL (No Click Count)
```bash
grpcurl -plaintext \
  -proto layered_simple/src/proto/urlshortener.proto \
  -import-path layered_simple/src/proto \
  -d '{"code": "YOUR_CODE", "count_click": false, "client_ip": "127.0.0.1"}' \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL
```

#### Get Top Links
```bash
grpcurl -plaintext \
  -proto layered_simple/src/proto/urlshortener.proto \
  -import-path layered_simple/src/proto \
  -d '{"limit": 5}' \
  localhost:8081 urlshort.v1.URLShortenerService.GetTopLinks
```

#### Get URL Statistics
```bash
grpcurl -plaintext \
  -proto layered_simple/src/proto/urlshortener.proto \
  -import-path layered_simple/src/proto \
  -d '{"code": "YOUR_CODE"}' \
  localhost:8081 urlshort.v1.URLShortenerService.GetStats
```

---

## 🔥 Complete Test Flow Scripts

### Microservices Test Script
Save as `test_microservices.sh`:

```bash
#!/bin/bash
echo "=== Creating Short URL ==="
RESPONSE=$(curl -s -X POST http://localhost:8080/shorten \
  -H "Content-Type: application/json" \
  -d '{"long_url":"https://www.github.com"}')

CODE=$(echo $RESPONSE | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
echo "Created code: $CODE"
echo "Short URL: http://localhost:8080/$CODE"

echo -e "\n=== Checking Redirect ==="
curl -I http://localhost:8080/$CODE

echo -e "\n=== Getting Analytics ==="
curl -s http://localhost:8080/analytics/top?limit=5 | jq
```

### Layered Test Script
Save as `test_layered.sh`:

```bash
#!/bin/bash
echo "=== Creating Short URL ==="
RESPONSE=$(grpcurl -plaintext \
  -proto layered_simple/src/proto/urlshortener.proto \
  -import-path layered_simple/src/proto \
  -d '{"long_url": "https://www.github.com", "client_ip": "127.0.0.1"}' \
  localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL)

CODE=$(echo "$RESPONSE" | sed -n 's/.*"code": *"\([^"]*\)".*/\1/p')
echo "Created code: $CODE"

echo -e "\n=== Resolving URL ==="
grpcurl -plaintext \
  -proto layered_simple/src/proto/urlshortener.proto \
  -import-path layered_simple/src/proto \
  -d "{\"code\": \"$CODE\", \"count_click\": true, \"client_ip\": \"127.0.0.1\"}" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL

echo -e "\n=== Getting Statistics ==="
grpcurl -plaintext \
  -proto layered_simple/src/proto/urlshortener.proto \
  -import-path layered_simple/src/proto \
  -d "{\"code\": \"$CODE\"}" \
  localhost:8081 urlshort.v1.URLShortenerService.GetStats

echo -e "\n=== Top Links ==="
grpcurl -plaintext \
  -proto layered_simple/src/proto/urlshortener.proto \
  -import-path layered_simple/src/proto \
  -d '{"limit": 5}' \
  localhost:8081 urlshort.v1.URLShortenerService.GetTopLinks
```

**Make executable:**
```bash
chmod +x test_microservices.sh test_layered.sh
```

---

## 📊 Feature Testing

### Test TTL Expiration
```bash
# Microservices
curl -X POST http://localhost:8080/shorten \
  -H "Content-Type: application/json" \
  -d '{"long_url":"https://test.com","ttl_sec":10}'

# Wait 11 seconds, then try to access (should get 404)
```

### Test Max Clicks
```bash
# Microservices
curl -X POST http://localhost:8080/shorten \
  -H "Content-Type: application/json" \
  -d '{"long_url":"https://test.com","max_clicks":3}'

# Access 4 times, 4th should fail with 410 Gone
```

### Test Rate Limiting
```bash
# Spam requests to trigger rate limit (120/minute default)
for i in {1..125}; do 
  curl -s http://localhost:8080/healthz > /dev/null
  echo "Request $i"
done
# Should see 429 Too Many Requests
```

---

## 🔍 Debugging & Logs

### View Logs
```bash
# Microservices - all services
docker-compose -f docker-compose.micro.yaml logs -f

# Microservices - specific service
docker-compose -f docker-compose.micro.yaml logs -f api-gateway

# Layered - all services
docker-compose -p layered -f docker-compose.layered.yaml logs -f
```

### Redis Direct Access
```bash
# Connect to Redis
docker exec -it compose-redis-1 redis-cli

# Check URLs
KEYS url:*
GET url:YOUR_CODE

# Check analytics
ZRANGE zset:clicks 0 -1 WITHSCORES

# Check rate limits
KEYS ratelimit:*

# Exit
exit
```

---

## 🎯 Port Reference

| Service | Port | Architecture |
|---------|------|--------------|
| Microservices API Gateway | 8080 | HTTP/REST |
| Layered API Gateway | 8081 | HTTP → gRPC |
| Redis | 6379 | Both |

---

## 📚 Key Features

✅ **5 Functional Requirements:**
1. Create short links
2. Resolve & redirect (HTTP 301)
3. Rate limiting (IP-based)
4. Top links analytics
5. Link expiration (TTL & max clicks)

✅ **Additional Features:**
- HEAD request support (check URL without consuming click)
- Health checks on all services
- Click tracking
- Redis persistence

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, gRPC
- **Database**: Redis (in-memory)
- **Containerization**: Docker & Docker Compose
- **Libraries**: Pydantic, httpx, redis-py, grpcio

---

## 📖 Architecture Comparison

| Feature | Microservices | Layered |
|---------|--------------|---------|
| **Communication** | HTTP/REST + JSON | gRPC + Protocol Buffers |
| **Coupling** | Loose | Tight |
| **Performance** | Good | Better (binary) |
| **Debugging** | Easier (readable JSON) | Harder (binary) |
| **Type Safety** | Runtime | Compile-time |
| **Scaling** | Independent services | Vertical layers |

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---
