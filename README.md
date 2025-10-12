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
