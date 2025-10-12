# CSE-5306-DS-PA2-URLShortener

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

A high-performance, distributed URL shortening service implementing both **Microservices** and **Layered** architectures for comparative analysis.

---

## 🎯 **Important: Testing Guide**

**All test commands are organized in dedicated txt files.** Follow these for step-by-step testing:

- 📘 [`microservices_http_runs.txt`](microservices_http_runs.txt) - Complete microservices testing guide
- 📙 [`layered_grpc_runs.txt`](layered_grpc_runs.txt) - Complete layered architecture testing guide
- 📊 [`loadtest_microservice_runs.txt`](loadtest_microservice_runs.txt) - HTTP load testing
- 📊 [`loadtest_layered_runs.txt`](loadtest_layered_runs.txt) - gRPC load testing

These files contain **all commands in the correct order** with expected outputs. Use them as your primary reference!

---

## 📑 Table of Contents
- [Important: Testing Guide](#-important-testing-guide)
- [What is URL Shortening?](#-what-is-url-shortening)
- [Key Features](#-key-features)
- [Project Structure](#-project-structure)
- [Functional Requirements](#-functional-requirements)
- [System Architectures](#️-system-architectures)
- [Getting Started](#-getting-started)
- [Testing](#-testing)
- [Architecture Comparison](#-architecture-comparison)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)
- [Quick Links](#-quick-links)

---

## 🌐 What is URL Shortening?

URL shortening transforms long, unwieldy URLs into short, manageable links while maintaining full functionality.

**Example:**
- Long URL: `https://www.example.com/very/long/path?id=12345`
- Short URL: `http://short.ly/abc123`
- User visits short URL → automatically redirected to long URL

---

## ✨ Key Features

- ✅ **Create Short Links** - Convert any URL to a 7-character code
- ✅ **Instant Redirection** - HTTP 301 redirects for optimal browser caching
- ✅ **Time-based Expiration** - Set TTL (time-to-live) for links
- ✅ **Click-based Expiration** - Limit number of uses per link
- ✅ **Rate Limiting** - Protect against abuse (120 req/min default)
- ✅ **Analytics** - Track click counts and view top links
- ✅ **HEAD Requests** - Check URLs without consuming click counts
- ✅ **High Availability** - Redis-backed persistence with optional replication

---

## 📁 Project Structure

```
CSE-5306-DS-PA2-URLShortener/
│
├── 📋 Test Files (Your Main Reference!)
│   ├── microservices_http_runs.txt      # All REST API test commands
│   ├── layered_grpc_runs.txt            # All gRPC test commands
│   ├── loadtest_microservice_runs.txt   # HTTP performance tests
│   └── loadtest_layered_runs.txt        # gRPC performance tests
│
├── 🔷 Microservices Architecture
│   ├── microservices_http/
│   │   ├── api_gateway/                 # HTTP Gateway (Port 8080)
│   │   ├── redirect_service/            # URL resolution
│   │   ├── analytics_service/           # Click tracking
│   │   └── ratelimit_service/           # Rate limiting
│   └── deploy/compose/
│       └── docker-compose.micro.yaml    # Microservices deployment
│
├── 🔷 Layered Architecture
│   └── layered_simple/
│       ├── src/
│       │   ├── proto/                   # gRPC definitions
│       │   ├── gateway/                 # API Layer (Port 8081)
│       │   ├── business/                # Logic Layer (Port 8082)
│       │   └── data/                    # Data Layer (Port 8083)
│       └── docker-compose.yaml          # Layered deployment
│
├── 🗄️ Common Components
│   ├── common/                          # Shared libraries
│   ├── persistence/                     # Redis repositories
│   └── deploy/                          # Deployment configs
│
└── 📄 Configuration
    ├── payload.json                     # Sample request payload
    └── README.md                        # This file
```

---

## 📋 Functional Requirements

### Requirement 1: Create Short Links
**What:** Convert long URLs into short codes  
**How:** 
- Accept long URL as input
- Generate unique 7-character code (base62 encoding)
- Store mapping in Redis
- Return short URL to user

**Example:**
```
Input:  "https://www.google.com"
Output: "http://localhost:8080/Vy6UJ4i"
```

---

### Requirement 2: Resolve & Redirect (HTTP 301)
**What:** Redirect users from short URL to original URL  
**How:**
- Lookup short code in Redis
- Return HTTP 301 redirect
- Increment analytics counter (for GET requests)
- Support HEAD requests (check without counting)

**Flow:**
```
User visits: http://localhost:8080/Vy6UJ4i
System finds: https://www.google.com
Browser redirects user to original URL
```

---

### Requirement 3: Rate Limiting
**What:** Prevent abuse and overload  
**How:**
- Track requests per IP address
- Default: 120 requests per minute per IP
- Sliding window algorithm
- Return HTTP 429 when limit exceeded

**Example:**
```
IP makes request #1-120:   ✓ Allowed
IP makes request #121:     ✗ Blocked (429 Too Many Requests)
After 60 seconds:          Counter resets
```

---

### Requirement 4: Top Links Analytics
**What:** Show most popular URLs  
**How:**
- Track click count per short code
- Maintain sorted set in Redis (O(log N) updates)
- Provide API to query top N links
- Real-time updates

**Example Output:**
```json
[
  {"code": "abc123", "clicks": 1523, "long_url": "https://example.com"},
  {"code": "xyz789", "clicks": 892, "long_url": "https://another.com"},
  {"code": "def456", "clicks": 654, "long_url": "https://third.com"}
]
```

---

### Requirement 5: Link Expiration
**What:** Automatic link expiration based on time or clicks  
**How:**

**Time-based (TTL):**
- Set expiration in seconds (e.g., 3600 = 1 hour)
- Redis handles automatic deletion
- Returns 404 after expiration

**Click-based (max_clicks):**
- Set maximum click count
- Atomic decrement on each access
- Returns 410 when limit reached

**Combined:**
- Both limits can be set
- Link expires when either limit hits

**Example:**
```json
{
  "long_url": "https://example.com",
  "ttl_sec": 3600,
  "max_clicks": 100
}
```

---

## 🏗️ System Architectures

### Architecture 1: Microservices (HTTP/REST)

**Concept:** Independent, loosely-coupled services communicating via HTTP

**Structure:**
```
🔷 API Gateway (Port 8080)
   - Routes requests to services
   - Aggregates responses
   - Single entry point

🔷 Redirect Service (Port 8001)
   - Creates short URLs
   - Resolves codes to long URLs
   - Manages expiration

🔷 Analytics Service (Port 8002)
   - Tracks click counts
   - Provides top links
   - Real-time statistics

🔷 Rate Limit Service (Port 8003)
   - Checks request limits
   - Enforces rate policies
   - Sliding window counters

🔷 Redis (Port 6379)
   - Shared data store
   - Persistence layer
```

**Communication:** HTTP/REST with JSON  
**Deployment:** Docker Compose (5 containers)

---

### Architecture 2: Layered (gRPC)

**Concept:** Vertical stack with strict layer separation and gRPC communication

**Structure:**
```
🔷 API Gateway Layer (Port 8081)
   - HTTP to gRPC translation
   - Client-facing interface
   - Request validation

🔷 Business Logic Layer (Port 8082)
   - URL validation
   - Code generation
   - Rate limit checks
   - Expiration logic

🔷 Data Service Layer (Port 8083)
   - Database operations
   - Redis communication
   - Data persistence

🔷 Redis Master (Port 6379)
   - Primary storage

🔷 Redis Replica (Port 6380)
   - Backup storage (optional)
```

**Communication:** gRPC with Protocol Buffers  
**Deployment:** Docker Compose (5 containers)

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- grpcurl (for gRPC testing) - Install: `brew install grpcurl` (Mac) or [grpcurl releases](https://github.com/fullstorydev/grpcurl/releases)
- curl (for REST testing) - Usually pre-installed

### Quick Start

#### **Option 1: Microservices Architecture (HTTP/REST)**

```bash
# 1. Clone repository
git clone https://github.com/AbhijitChallapalli/CSE-5306-DS-PA2-URLShortener.git
cd CSE-5306-DS-PA2-URLShortener

# 2. Start services (builds automatically)
docker-compose -f deploy/compose/docker-compose.micro.yaml up --build

# 3. Wait for services to be ready (~30 seconds)

# 4. Follow testing commands in microservices_http_runs.txt
```

**Service URLs:**
- API Gateway: http://localhost:8080
- Health Check: http://localhost:8080/healthz

---

#### **Option 2: Layered Architecture (gRPC)**

```bash
# 1. Clone repository (if not already done)
git clone https://github.com/AbhijitChallapalli/CSE-5306-DS-PA2-URLShortener.git
cd CSE-5306-DS-PA2-URLShortener/layered_simple

# 2. Start services (builds automatically)
docker-compose up --build

# 3. Wait for services to be ready (~30 seconds)

# 4. Follow testing commands in layered_grpc_runs.txt
```

**Service URLs:**
- gRPC Gateway: localhost:8081
- Business Logic: localhost:8082
- Data Service: localhost:8083

---

### 📋 Next Steps

After starting your chosen architecture:

1. Open the appropriate test file:
   - **Microservices**: `microservices_http_runs.txt`
   - **Layered**: `layered_grpc_runs.txt`

2. Run the commands in order - they're designed to work sequentially

3. For performance testing, see the load test files after basic tests work

---

## 🧪 Testing

> **💡 TIP:** All test commands are organized in dedicated txt files. **Use these files as your primary testing guide** - they contain complete, ordered test sequences with expected outputs!

### 📋 Test Files - Your Complete Testing Guide

**Microservices Architecture (HTTP/REST) - Port 8080**
- 📘 **[`microservices_http_runs.txt`](microservices_http_runs.txt)** - Complete testing guide
  - Create short URLs (basic, with TTL, with max_clicks)
  - Resolve URLs (GET and HEAD requests)
  - Get analytics and top links
  - Health checks
  - ✅ All commands in proper order with examples

- 📊 **[`loadtest_microservice_runs.txt`](loadtest_microservice_runs.txt)** - Performance testing
  - Apache Bench (ab) commands
  - Performance benchmarking
  - Concurrent request testing

**Layered Architecture (gRPC) - Ports 8081-8083**
- 📙 **[`layered_grpc_runs.txt`](layered_grpc_runs.txt)** - Complete testing guide
  - grpcurl commands for all operations
  - CreateShortURL, ResolveURL, GetTopLinks, GetStats
  - Complete test flows with examples
  - ✅ All commands in proper order with examples

- 📊 **[`loadtest_layered_runs.txt`](loadtest_layered_runs.txt)** - Performance testing
  - ghz commands for gRPC load testing
  - Performance benchmarking
  - Concurrent request testing

---

### 🚀 Quick Example (Just to Verify It Works)

**Want a 30-second smoke test?** Try these minimal commands:

**Microservices (HTTP):**
```bash
# Create a short URL
curl -X POST http://localhost:8080/shorten \
  -H "Content-Type: application/json" \
  -d '{"long_url":"https://www.google.com"}'

# Response: {"code":"abc123","short_url":"http://localhost:8080/abc123"}

# Visit the short URL (use the code from response above)
curl -I http://localhost:8080/abc123
```

**Layered (gRPC):**
```bash
# Create a short URL
grpcurl -plaintext \
  -proto layered_simple/src/proto/urlshortener.proto \
  -import-path layered_simple/src/proto \
  -d '{"long_url": "https://www.google.com", "client_ip": "127.0.0.1"}' \
  localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL

# Response: {"code": "xyz789", "shortUrl": "http://localhost:8081/xyz789"}
```

✅ **If these work, proceed to the complete test files above for full testing!**

---

## 📊 Architecture Comparison

### Performance & Trade-offs

Both architectures are fully implemented and tested. For detailed performance comparisons:

- **Microservices Load Tests**: See [`loadtest_microservice_runs.txt`](loadtest_microservice_runs.txt)
- **Layered Load Tests**: See [`loadtest_layered_runs.txt`](loadtest_layered_runs.txt)

### Key Differences

| Aspect | Microservices (HTTP/REST) | Layered (gRPC) |
|--------|---------------------------|----------------|
| **Communication** | HTTP/REST with JSON | gRPC with Protocol Buffers |
| **Testing Tool** | curl, Apache Bench (ab) | grpcurl, ghz |
| **Port** | 8080 (single gateway) | 8081, 8082, 8083 (multiple) |
| **Service Discovery** | Environment variables | Direct gRPC connections |
| **Serialization** | JSON (text-based) | Protobuf (binary) |
| **Independence** | High - services fully decoupled | Lower - tight layer coupling |
| **Scalability** | Easier horizontal scaling | Better vertical performance |
| **Debugging** | Easy with browser/curl | Requires grpcurl/tools |
| **Type Safety** | Runtime validation (Pydantic) | Compile-time (Protobuf) |

### When to Use Each

**Choose Microservices when:**
- Building large, complex systems with many teams
- Need language/technology diversity
- Services have different scaling requirements
- Prefer REST/HTTP simplicity
- Building public APIs

**Choose Layered when:**
- Need maximum performance (lower latency)
- Building internal systems with one team
- Want strong typing and contracts
- Network efficiency is critical
- All services use compatible languages

---

## 🔧 Troubleshooting

### Services won't start?
1. Check if ports are already in use:
   ```bash
   # Microservices uses: 8080, 6379
   # Layered uses: 8081, 8082, 8083, 6379
   lsof -i :8080  # Check if port is in use
   ```

2. Stop and rebuild:
   ```bash
   docker-compose down -v
   docker-compose up --build
   ```

### Commands not working?
1. **First check the test files!** They contain the correct, tested commands:
   - `microservices_http_runs.txt` for REST API
   - `layered_grpc_runs.txt` for gRPC

2. Verify services are healthy:
   ```bash
   # Microservices
   curl http://localhost:8080/healthz
   
   # Layered
   grpcurl -plaintext localhost:8081 grpc.health.v1.Health/Check
   ```

3. Check Docker logs:
   ```bash
   docker-compose logs -f
   ```

### Need grpcurl?
```bash
# macOS
brew install grpcurl

# Linux
wget https://github.com/fullstorydev/grpcurl/releases/download/v1.8.9/grpcurl_1.8.9_linux_x86_64.tar.gz
tar -xvf grpcurl_1.8.9_linux_x86_64.tar.gz
sudo mv grpcurl /usr/local/bin/
```

---

## 🤝 Contributing

Contributions are welcome! If you find issues or have suggestions:

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

---

## 🎓 Academic Context

This project was developed as Programming Assignment 2 for CSE 5306 (Distributed Systems) at the University of Texas at Arlington. It demonstrates:

- ✅ Distributed system design patterns
- ✅ Microservices vs Layered architectures
- ✅ RESTful and gRPC communication
- ✅ Containerization and orchestration
- ✅ Performance evaluation and trade-off analysis
- ✅ Production-ready distributed system implementation

---

## 🔗 Quick Links

### **📋 Testing Guides (Start Here!)**
- [Microservices HTTP Tests](microservices_http_runs.txt) - All REST API commands
- [Layered gRPC Tests](layered_grpc_runs.txt) - All gRPC commands
- [HTTP Load Tests](loadtest_microservice_runs.txt) - Performance benchmarking
- [gRPC Load Tests](loadtest_layered_runs.txt) - Performance benchmarking

### **📚 Documentation**
- [GitHub Repository](https://github.com/AbhijitChallapalli/CSE-5306-DS-PA2-URLShortener)
- [Docker Compose Files](deploy/compose/)
- [API Gateway Code](microservices_http/api_gateway/)
- [gRPC Proto Files](layered_simple/src/proto/)

---

> **📌 Remember:** For the best testing experience, follow the commands in the txt files above. They're organized, tested, and include expected outputs!

---

**Last Updated**: October 2025  
**Author**: Abhijit Challapalli | University of Texas at Arlington | CSE 5306
