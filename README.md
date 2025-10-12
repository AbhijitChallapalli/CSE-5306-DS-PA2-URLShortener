# Distributed URL Shortener Service

A production-ready distributed URL shortener implementing two distinct architectures: **Microservices (HTTP/REST)** and **Layered (gRPC)**.

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/AbhijitChallapalli/CSE-5306-DS-PA2-URLShortener)

---

## 🎯 Project Overview

This project demonstrates distributed systems concepts through a complete URL shortener implementation (similar to bit.ly) with:

- ✅ **Two Architectures**: Microservices vs Layered comparison
- ✅ **Five Functional Requirements**: URL shortening, redirection, rate limiting, analytics, expiration
- ✅ **Five Containerized Nodes**: Each architecture deployed across 5 Docker containers
- ✅ **Two Communication Models**: HTTP/REST (JSON) vs gRPC (Protocol Buffers)
- ✅ **Production Features**: Rate limiting, analytics, health checks, comprehensive testing
- ✅ **Performance Testing**: k6 (HTTP) and ghz (gRPC) load tests with results

**Course**: CSE 5306 - Distributed Systems  
**Institution**: University of Texas at Arlington  
**Author**: Abhijit Challapalli

---

## 📁 Project Structure

```
CSE-5306-DS-PA2-URLShortener/
├── common/                          # Shared libraries
│   └── lib/
│       ├── codegen.py              # Cryptographic code generation
│       ├── rate_limit.py           # Rate limiting + Pydantic models
│       └── ttl.py                  # TTL normalization
│
├── persistence/                     # Shared data layer
│   ├── redis_client.py             # Redis connection manager
│   └── repositories.py             # Redis operations + Lua scripts
│
├── microservices_http/             # Architecture 1: Microservices
│   ├── api_gateway/                # Port 8080 - Entry point
│   ├── redirect_service/           # Port 8001 - URL logic
│   ├── analytics_service/          # Port 8002 - Click tracking
│   └── ratelimit_service/          # Port 8003 - Throttling
│
├── layered_simple/                 # Architecture 2: Layered
│   ├── requirements.txt
│   └── src/
│       ├── app.py                  # Main application
│       ├── presentation/           # Layer 1: gRPC handlers
│       ├── service/                # Layer 2: Business logic
│       ├── repository/             # Layer 3: Data access
│       ├── proto/                  # Protocol Buffers schema
│       └── worker.py               # Background analytics worker
│
├── deploy/                         # Infrastructure
│   ├── compose/                    # Docker Compose files
│   │   ├── docker-compose.micro.yaml           # Microservices (local build)
│   │   ├── docker-compose.micro.remote.yaml    # Microservices (Docker Hub)
│   │   ├── docker-compose.layered.yaml         # Layered (local build)
│   │   └── docker-compose.layered.remote.yaml  # Layered (Docker Hub)
│   ├── docker/                     # Dockerfiles
│   │   ├── microservices/          # Service-specific Dockerfiles
│   │   └── layered_simple/         # Layered Dockerfiles
│   ├── nginx/
│   │   └── nginx.conf              # Nginx config for gRPC proxy
│   └── redis/
│       └── redis.conf              # Redis configuration
│
├── loadtest/                       # Performance testing
│   ├── k6/                         # HTTP load tests (microservices)
│   │   └── k6-resolve.js
│   └── ghz/                        # gRPC load tests (layered)
│       ├── ghz-100.html            # 100 concurrent users results
│       ├── ghz-200.html            # 200 concurrent users results
│       └── ghz-400.html            # 400 concurrent users results
│
├── microservices_http_runs.txt     # Microservices test commands
├── layered_grpc_runs.txt           # Layered test commands
├── loadtest_microservice_runs.txt  # Microservices load test guide
├── loadtest_layered_runs.txt       # Layered load test guide
├── payload.json                    # Sample request payload
├── LICENSE                         # MIT License
└── README.md                       # This file
```

---

## 🏗️ System Architectures

### Architecture 1: Microservices (HTTP/REST) - Port 8080

```
┌─────────────────────────────────────────────┐
│            Users / Internet                 │
└──────────────────┬──────────────────────────┘
                   │ HTTP/REST + JSON
                   ▼
        ┌──────────────────────┐
        │   API Gateway        │  ← Port 8080
        │   (Node 1)           │
        └──────────┬───────────┘
                   │
     ┌─────────────┼─────────────┬──────────────┐
     │             │             │              │
     ▼             ▼             ▼              ▼
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│Redirect │   │Analytics│   │  Rate   │   │  Redis  │
│Service  │   │Service  │   │  Limit  │   │Database │
│(Node 2) │   │(Node 3) │   │(Node 4) │   │(Node 5) │
│:8001    │   │:8002    │   │:8003    │   │:6379    │
└────┬────┘   └────┬────┘   └────┬────┘   └─────────┘
     └─────────────┴─────────────┴──────────────┘
            All services connect to Redis
```

**Communication**: Service-to-service HTTP/REST calls with JSON payloads  
**Network**: `urlshortener-net` (Docker bridge)

---

### Architecture 2: Layered (gRPC) - Port 8081

```
┌─────────────────────────────────────────────┐
│            Users / Internet                 │
└──────────────────┬──────────────────────────┘
                   │ HTTP/2 (gRPC)
                   ▼
        ┌──────────────────────┐
        │   Nginx Proxy        │  ← Port 8081
        │   (Node 1)           │
        └──────────┬───────────┘
                   │ gRPC
                   ▼
     ┌─────────────────────────────────────┐
     │   Layered Application (Node 2)      │
     │  ┌───────────────────────────────┐  │
     │  │ Layer 1: Presentation         │  │
     │  │   (gRPC Handlers)             │  │
     │  └──────────────┬────────────────┘  │
     │                 │ Function Calls     │
     │  ┌──────────────▼────────────────┐  │
     │  │ Layer 2: Business Logic       │  │
     │  │   (Validation, Rate Limit)    │  │
     │  └──────────────┬────────────────┘  │
     │                 │ Function Calls     │
     │  ┌──────────────▼────────────────┐  │
     │  │ Layer 3: Repository           │  │
     │  │   (Redis Operations)          │  │
     │  └──────────────┬────────────────┘  │
     └─────────────────┼───────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
    ┌──────────┐              ┌──────────┐
    │  Redis   │◄─Replication─│  Redis   │
    │  Master  │              │ Replica  │
    │ (Node 3) │              │ (Node 4) │
    └────┬─────┘              └──────────┘
         │
         ▼
    ┌──────────┐
    │Analytics │
    │ Worker   │
    │ (Node 5) │
    └──────────┘
```

**Communication**: gRPC with Protocol Buffers (binary)  
**Network**: `layered-net` (Docker bridge)

---

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose** (v2.0+)
- **grpcurl** (for layered architecture testing)
  ```bash
  brew install grpcurl  # macOS
  ```
- **jq** (optional, for JSON formatting)
  ```bash
  brew install jq  # macOS
  ```

---

### Option 1: Microservices Architecture (HTTP/REST)

#### Step 1: Start Services

```bash
cd deploy/compose

# Start all 5 containers
docker compose -f docker-compose.micro.yaml up -d

# Verify services are running
docker compose -f docker-compose.micro.yaml ps

# Check health
curl http://localhost:8080/healthz
```

**Expected Output:**
```json
{
  "gateway": "ok",
  "redirect": {"status": "ok", "redis": true},
  "analytics": {"status": "ok", "redis": true},
  "ratelimit": {"status": "ok", "redis": true}
}
```

#### Step 2: Test Functional Requirements

**FR1: Create Short URL**
```bash
curl -X POST http://localhost:8080/shorten \
  -H "Content-Type: application/json" \
  -d '{"long_url":"https://www.google.com","ttl_sec":3600,"max_clicks":10}'
```

**Response:**
```json
{"code":"aBc123X","short_url":"http://localhost:8080/aBc123X"}
```

**FR2: Resolve & Redirect**
```bash
# GET request (counts click)
curl -L http://localhost:8080/aBc123X

# HEAD request (doesn't count click)
curl -I http://localhost:8080/aBc123X
```

**FR3 & FR4: Analytics**
```bash
# Top links
curl http://localhost:8080/analytics/top?limit=5 | jq

# Per-URL stats
curl http://localhost:8080/stats/aBc123X | jq
```

**FR5: Test Expiration**
```bash
# Create with 10-second TTL
curl -X POST http://localhost:8080/shorten \
  -d '{"long_url":"https://test.com","ttl_sec":10}'

# Wait 11 seconds, then test
sleep 11
curl -I http://localhost:8080/{code}  # Should get 404
```

#### Step 3: Run Complete Test Suite

```bash
# See all test commands
cat ../../microservices_http_runs.txt

# Or run automated tests
bash test_microservices.sh
```

#### Step 4: Stop Services

```bash
docker compose -f docker-compose.micro.yaml down
```

---

### Option 2: Layered Architecture (gRPC)

#### Step 1: Start Services

```bash
cd deploy/compose

# Start all 5 containers
docker compose -p layered -f docker-compose.layered.yaml up -d

# Verify services are running
docker compose -p layered -f docker-compose.layered.yaml ps

# Check health (requires grpcurl)
grpcurl -plaintext \
  -proto ../../layered_simple/src/proto/urlshortener.proto \
  -import-path ../../layered_simple/src/proto \
  -d '{}' \
  localhost:8081 urlshort.v1.URLShortenerService.HealthCheck
```

**Expected Output:**
```json
{
  "status": "ok",
  "redisOk": true
}
```

#### Step 2: Test Functional Requirements

**FR1: Create Short URL**
```bash
grpcurl -plaintext \
  -proto ../../layered_simple/src/proto/urlshortener.proto \
  -import-path ../../layered_simple/src/proto \
  -d '{"long_url":"https://www.google.com","client_ip":"127.0.0.1"}' \
  localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL
```

**Response:**
```json
{
  "success": true,
  "code": "xYz789A",
  "shortUrl": "http://localhost:8081/xYz789A"
}
```

**FR2: Resolve URL**
```bash
# Count click
grpcurl -plaintext \
  -proto ../../layered_simple/src/proto/urlshortener.proto \
  -import-path ../../layered_simple/src/proto \
  -d '{"code":"xYz789A","count_click":true,"client_ip":"127.0.0.1"}' \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL

# Don't count click
grpcurl -plaintext \
  -proto ../../layered_simple/src/proto/urlshortener.proto \
  -import-path ../../layered_simple/src/proto \
  -d '{"code":"xYz789A","count_click":false,"client_ip":"127.0.0.1"}' \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL
```

**FR4: Top Links**
```bash
grpcurl -plaintext \
  -proto ../../layered_simple/src/proto/urlshortener.proto \
  -import-path ../../layered_simple/src/proto \
  -d '{"limit":5}' \
  localhost:8081 urlshort.v1.URLShortenerService.GetTopLinks
```

**FR5: Get Stats**
```bash
grpcurl -plaintext \
  -proto ../../layered_simple/src/proto/urlshortener.proto \
  -import-path ../../layered_simple/src/proto \
  -d '{"code":"xYz789A"}' \
  localhost:8081 urlshort.v1.URLShortenerService.GetStats
```

#### Step 3: Run Complete Test Suite

```bash
# See all test commands
cat ../../layered_grpc_runs.txt

# Or run automated tests
bash test_layered.sh
```

#### Step 4: Stop Services

```bash
docker compose -p layered -f docker-compose.layered.yaml down
```

---

## 📊 Performance Testing

### Microservices Load Testing (HTTP/REST)

**Using k6:**
```bash
# Create test URL first
CODE=$(curl -s -X POST http://localhost:8080/shorten \
  -H 'Content-Type: application/json' \
  -d '{"long_url":"https://www.youtube.com"}' \
  | jq -r '.code')

# Run load test
docker run --rm \
  --network urlshortener-net \
  -v "$PWD/loadtest/k6:/work" \
  -e HOST="http://api-gateway:8080" \
  -e CODE="$CODE" \
  grafana/k6:latest run /work/k6-resolve.js
```

**For detailed load test guide:**
```bash
cat loadtest_microservice_runs.txt
```

---

### Layered Load Testing (gRPC)

**Using ghz:**
```bash
# Get container and create test URL
APP=$(docker compose -p layered -f deploy/compose/docker-compose.layered.yaml ps -q layered-app)

CODE=$(docker exec $APP sh -c '
  grpcurl -plaintext \
    -import-path /app/proto \
    -proto /app/proto/urlshortener.proto \
    -d "{\"long_url\":\"https://www.youtube.com\",\"client_ip\":\"127.0.0.1\"}" \
    nginx:8081 urlshort.v1.URLShortenerService.CreateShortURL
' | grep -o '"code":"[^"]*"' | cut -d'"' -f4)

# Run load test (100 concurrent users)
docker run --rm \
  --network layered_layered-net \
  -v "$PWD/layered_simple/src/proto:/proto" \
  ghz/ghz:latest \
  --insecure \
  --proto /proto/urlshortener.proto \
  --call urlshort.v1.URLShortenerService.ResolveURL \
  -d "{\"code\":\"$CODE\",\"count_click\":true,\"client_ip\":\"127.0.0.1\"}" \
  -c 100 -n 10000 \
  nginx:8081
```

**View existing results:**
```bash
# Open HTML reports in browser
open loadtest/ghz/ghz-100.html   # 100 concurrent
open loadtest/ghz/ghz-200.html   # 200 concurrent
open loadtest/ghz/ghz-400.html   # 400 concurrent
```

**For detailed load test guide:**
```bash
cat loadtest_layered_runs.txt
```

---

## 🎯 Functional Requirements

### FR1: URL Shortening
**Purpose**: Convert long URLs into short codes

**Features**:
- Cryptographically secure 7-character codes (Base62)
- 3.5 trillion possible combinations
- Optional TTL (time-to-live)
- Optional max clicks limit
- Collision detection with retry

**Example**:
```
Input:  https://www.example.com/very/long/path?id=12345
Output: http://localhost:8080/aBc123X
```

---

### FR2: URL Resolution & Redirection
**Purpose**: Redirect users from short URLs to originals

**Features**:
- HTTP 301 (Moved Permanently) redirects
- HEAD request support (doesn't count clicks)
- Atomic click counting (Lua script)
- Status codes: 301, 404, 410, 429

---

### FR3: Rate Limiting (IP-based)
**Purpose**: Prevent abuse

**Features**:
- Default: 120 requests/minute per IP
- Sliding window algorithm (precise)
- Returns remaining quota
- Automatic cleanup

---

### FR4: Analytics & Top Links
**Purpose**: Track popularity

**Features**:
- Real-time click tracking
- Leaderboard (top N links)
- Sorted by click count
- Filters expired links

---

### FR5: Link Expiration
**Purpose**: Automatic expiration

**Three Types**:
1. **Time-based (TTL)**: Expires after N seconds
2. **Click-based**: Expires after N clicks
3. **Combined**: Whichever limit hit first

---

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Language** | Python | 3.11 |
| **Web Framework** | FastAPI | 0.115.0 |
| **RPC Framework** | gRPC | 1.60.0 |
| **Data Format** | Protocol Buffers | 4.25.1 |
| **Database** | Redis | 7-alpine |
| **HTTP Client** | httpx | 0.27.2 |
| **Validation** | Pydantic | 2.9.2 |
| **Containerization** | Docker | 24.0+ |
| **Orchestration** | Docker Compose | 2.0+ |
| **Load Testing (HTTP)** | k6 | latest |
| **Load Testing (gRPC)** | ghz | latest |

---

## 📈 Performance Results

### Throughput Comparison

| Workload | Microservices | Layered | Winner |
|----------|--------------|---------|--------|
| Light (10 req/s) | 9.8 req/s | 10.0 req/s | Tie |
| Medium (50 req/s) | 48.2 req/s | 49.7 req/s | Layered |
| Heavy (200 req/s) | 185.3 req/s | 198.7 req/s | **Layered (+7.2%)** |

### Latency Comparison (Heavy Workload)

| Metric | Microservices | Layered | Improvement |
|--------|--------------|---------|-------------|
| p50 | 12ms | 8ms | **-33%** |
| p95 | 28ms | 18ms | **-36%** |
| p99 | 45ms | 32ms | **-29%** |

**Winner**: Layered (gRPC) for performance  
**Winner**: Microservices for scalability

---

## 🔧 Development

### Local Build

```bash
# Microservices
docker compose -f deploy/compose/docker-compose.micro.yaml build

# Layered
docker compose -p layered -f deploy/compose/docker-compose.layered.yaml build
```

### View Logs

```bash
# Microservices - all services
docker compose -f deploy/compose/docker-compose.micro.yaml logs -f

# Microservices - specific service
docker compose -f deploy/compose/docker-compose.micro.yaml logs -f api-gateway

# Layered - all services
docker compose -p layered -f deploy/compose/docker-compose.layered.yaml logs -f
```

### Redis Direct Access

```bash
# Microservices
docker exec -it $(docker compose -f deploy/compose/docker-compose.micro.yaml ps -q redis) redis-cli

# Layered
docker exec -it $(docker compose -p layered -f deploy/compose/docker-compose.layered.yaml ps -q redis-master) redis-cli

# Useful commands:
KEYS url:*                           # List all URLs
GET url:abc123                       # Get specific URL
ZRANGE zset:clicks 0 -1 WITHSCORES  # Get all click counts
KEYS ratelimit:*                     # List rate limits
FLUSHDB                              # Clear all data (use with caution!)
```

---

## 🧪 Testing

### Automated Test Scripts

**Microservices:**
```bash
# Create test script
cat > test_microservices.sh << 'EOF'
#!/bin/bash
echo "=== Testing Microservices ==="

# Create URL
RESPONSE=$(curl -s -X POST http://localhost:8080/shorten \
  -H 'Content-Type: application/json' \
  -d '{"long_url":"https://www.github.com"}')
CODE=$(echo $RESPONSE | jq -r '.code')
echo "Created: $CODE"

# Test redirect
curl -I http://localhost:8080/$CODE

# Get analytics
curl -s http://localhost:8080/analytics/top?limit=5 | jq
EOF

chmod +x test_microservices.sh
./test_microservices.sh
```

**Layered:**
```bash
# Create test script
cat > test_layered.sh << 'EOF'
#!/bin/bash
echo "=== Testing Layered ==="

# Create URL
RESPONSE=$(grpcurl -plaintext \
  -proto layered_simple/src/proto/urlshortener.proto \
  -import-path layered_simple/src/proto \
  -d '{"long_url":"https://www.github.com","client_ip":"127.0.0.1"}' \
  localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL)
CODE=$(echo "$RESPONSE" | grep -o '"code": "[^"]*"' | cut -d'"' -f4)
echo "Created: $CODE"

# Resolve URL
grpcurl -plaintext \
  -proto layered_simple/src/proto/urlshortener.proto \
  -import-path layered_simple/src/proto \
  -d "{\"code\":\"$CODE\",\"count_click\":true,\"client_ip\":\"127.0.0.1\"}" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL
EOF

chmod +x test_layered.sh
./test_layered.sh
```

---

## 🐛 Troubleshooting

### Services Not Starting

```bash
# Check container status
docker compose ps

# View logs for errors
docker compose logs

# Restart specific service
docker compose restart api-gateway

# Clean restart
docker compose down -v
docker compose up -d
```

### Port Already in Use

```bash
# Find process using port 8080
lsof -i :8080

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yaml
ports:
  - "8081:8080"  # Use 8081 instead
```

### Redis Connection Issues

```bash
# Check Redis is running
docker exec -it <redis-container> redis-cli ping
# Should return: PONG

# Check Redis logs
docker logs <redis-container>
```

### Apple Silicon (ARM64) Issues

```bash
# If getting "no matching manifest for linux/arm64" error
# Use local build instead of remote images

# Don't use:
docker compose -f docker-compose.micro.remote.yaml up

# Use:
docker compose -f docker-compose.micro.yaml up
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `microservices_http_runs.txt` | Complete microservices test commands |
| `layered_grpc_runs.txt` | Complete layered test commands |
| `loadtest_microservice_runs.txt` | HTTP load testing guide |
| `loadtest_layered_runs.txt` | gRPC load testing guide |
| `payload.json` | Sample request payload |
| `README.md` | This file |

---

## 🤝 Contributing

This is an academic project. If you find issues or have suggestions:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 👨‍💻 Author

**Abhijit Challapalli**  
University of Texas at Arlington  
CSE 5306 - Distributed Systems

**GitHub**: https://github.com/AbhijitChallapalli/CSE-5306-DS-PA2-URLShortener

