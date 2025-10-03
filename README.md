# CSE-5306-DS-PA2-URLShortener
This repository contains the design and implementation of our own distributed system(URL Shortener). This implementation is done using two architectures 1) Microservices 2) Layered


**Example:**
- Long URL: `https://www.example.com/very/long/path?id=12345`
- Short URL: `http://short.ly/abc123`
- User visits short URL → automatically redirected to long URL


### 1. Five Functional Requirements

#### Requirement 1: Create Short Links
**What:** Convert long URLs into short codes  
**How:** 
- Take long URL as input
- Generate unique 6-character code (using hash or random)
- Store mapping in database
- Return short URL to user

**Example Flow:**
```
User sends: "https://www.google.com"
System generates: "abc123"
System returns: "http://localhost:8080/abc123"
```

---

#### Requirement 2: Resolve & Redirect (HTTP 301)
**What:** When user visits short URL, send them to original URL  
**How:**
- User visits short URL
- System looks up short code in database
- Find original long URL
- Return HTTP 301 redirect
- Increment click counter

**Example Flow:**
```
User visits: http://localhost:8080/abc123
System looks up: abc123 → https://www.google.com
Browser redirects to: https://www.google.com
Counter: abc123 clicks = 1 → 2
```

---

#### Requirement 3: Rate Limiting
**What:** Prevent users from spamming our service  
**How:**
- Track requests per IP address
- Set limit (e.g., 100 requests per minute)
- Block requests that exceed limit
- Return error message when blocked

**Two Types:**
1. **IP-based:** Max 100 requests/minute per IP
2. **Global:** Max 10,000 requests/minute for entire system

**Example Flow:**
```
IP 192.168.1.1 makes request #1-99: ✓ Allowed
IP 192.168.1.1 makes request #100: ✓ Allowed
IP 192.168.1.1 makes request #101: ✗ Blocked (429 Too Many Requests)
After 1 minute: Counter resets, IP can make requests again
```

---

#### Requirement 4: Top Links Analytics
**What:** Show most popular/clicked URLs  
**How:**
- Track click count for each short code
- Maintain sorted list by popularity
- Provide API endpoint to get top N links
- Update in real-time as clicks happen

**Example Output:**
```
Top 5 Links:
1. abc123 → 1,523 clicks → https://example.com
2. xyz789 → 892 clicks → https://another.com
3. def456 → 654 clicks → https://third.com
4. ghi012 → 432 clicks → https://fourth.com
5. jkl345 → 289 clicks → https://fifth.com
```

---

#### Requirement 5: Link Expiration
**What:** Links can expire based on time or click count  
**How:**

**Time-based Expiration:**
- User creates link with TTL (time-to-live) = 3600 seconds
- After 3600 seconds, link stops working
- System automatically deletes expired links

**Click-based Expiration:**
- User creates link with max_clicks = 50
- After 50 clicks, link stops working
- System prevents further access

**Combined:**
- Can set both: TTL AND max_clicks
- Whichever limit hits first, link expires

**Example:**
```
Create link with TTL=1 hour, max_clicks=100
- Scenario 1: 1 hour passes → link expires (even if only 20 clicks)
- Scenario 2: 100 clicks reached in 30 min → link expires (before 1 hour)
```

---

## 🏗️ Two System Architectures

### Architecture 1: Layered (3-Tier) with gRPC

#### Concept: Vertical Stack
Think of it like a **multi-floor building** where requests flow from top to bottom.

#### Structure:
```
🔷 Layer 1: API Gateway (Node 1)
   - Faces the users
   - Handles HTTP requests/responses
   - Converts HTTP → gRPC

🔷 Layer 2: Business Logic (Node 2)
   - Validates URLs
   - Generates short codes
   - Checks rate limits
   - Enforces expiration rules

🔷 Layer 3: Data Service (Node 3)
   - Talks to database
   - Stores/retrieves URLs
   - Manages counters

🔷 Storage: Redis Database (Nodes 4 & 5)
   - Master-Replica setup
   - Stores all data
```

#### Communication: gRPC
- **What:** Binary protocol (not text/JSON)
- **Why:** Fast, efficient, type-safe
- **How:** Define Protocol Buffers (like API contracts)

#### Flow Example:
```
User → API Gateway (HTTP)
       ↓
API Gateway → Business Logic (gRPC call)
              ↓
Business Logic → Data Service (gRPC call)
                 ↓
Data Service → Redis (database call)
               ↓
Response flows back up
```

#### 5 Nodes:
1. API Gateway (Presentation)
2. Business Logic (Processing)
3. Data Service (Persistence)
4. Redis Master (Primary storage)
5. Redis Replica (Backup storage)



### Architecture 2: Microservices with HTTP/REST

#### Concept: Independent Services
Think of it like a **food court** where each restaurant operates independently.

#### Structure:
```
🔷 API Gateway (Node 1)
   - Routes requests to appropriate service
   - Aggregates responses if needed

🔷 Redirect Service (Node 2)
   - Handles URL resolution
   - Performs redirects
   - Manages URL storage

🔷 Analytics Service (Node 3)
   - Tracks click counts
   - Provides top links
   - Aggregates statistics

🔷 Rate Limit Service (Node 4)
   - Checks request limits
   - Blocks excessive requests
   - Manages rate counters

🔷 Redis (Node 5)
   - Shared database for all services
```

#### Communication: HTTP/REST
- **What:** Standard web protocol with JSON
- **Why:** Universal, easy to debug, loosely coupled
- **How:** Each service exposes REST API endpoints

#### Flow Example:
```
User → API Gateway (HTTP)
       ↓
Gateway → Redirect Service (HTTP) \
       → Analytics Service (HTTP)  → All talk to Redis
       → Rate Limit Service (HTTP)/
```

#### 5 Nodes:
1. API Gateway (Routing)
2. Redirect Service (URL resolution)
3. Analytics Service (Statistics)
4. Rate Limit Service (Protection)
5. Redis (Shared storage)
