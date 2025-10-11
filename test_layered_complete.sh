#!/bin/bash

PROTO_PATH="layered_simple/src/proto"
PROTO_FILE="$PROTO_PATH/urlshortener.proto"

echo "🚀 Testing Layered Architecture"
echo "================================"

# Test 1: Health Check
echo -e "\n✅ Test 1: Health Check"
grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d '{}' \
  localhost:8081 urlshort.v1.URLShortenerService.HealthCheck

# Test 2: Create Short URL
echo -e "\n✅ Test 2: Create Short URL"
RESPONSE=$(grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d '{
    "long_url": "https://www.google.com",
    "ttl_sec": 3600,
    "max_clicks": 10,
    "client_ip": "127.0.0.1"
  }' \
  localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL)

echo "$RESPONSE"

# Extract code
CODE=$(echo $RESPONSE | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
echo -e "\n📝 Created code: $CODE"

# Test 3: Resolve URL
echo -e "\n✅ Test 3: Resolve URL"
grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d "{
    \"code\": \"$CODE\",
    \"count_click\": true,
    \"client_ip\": \"127.0.0.1\"
  }" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL

# Test 4: Create more URLs
echo -e "\n✅ Test 4: Creating more URLs for analytics"
grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d '{
    "long_url": "https://www.facebook.com",
    "client_ip": "127.0.0.1"
  }' \
  localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL > /dev/null

grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d '{
    "long_url": "https://www.twitter.com",
    "client_ip": "127.0.0.1"
  }' \
  localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL > /dev/null

# Resolve them to generate clicks
grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d "{
    \"code\": \"$CODE\",
    \"count_click\": true,
    \"client_ip\": \"127.0.0.1\"
  }" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL > /dev/null

# Test 5: Get Top Links
echo -e "\n✅ Test 5: Get Top Links"
grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d '{"limit": 5}' \
  localhost:8081 urlshort.v1.URLShortenerService.GetTopLinks

# Test 6: Get Stats
echo -e "\n✅ Test 6: Get Statistics"
grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d "{\"code\": \"$CODE\"}" \
  localhost:8081 urlshort.v1.URLShortenerService.GetStats

# Test 7: TTL Expiration
echo -e "\n✅ Test 7: TTL Expiration (5 seconds)"
RESPONSE=$(grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d '{
    "long_url": "https://www.expiretest.com",
    "ttl_sec": 5,
    "client_ip": "127.0.0.1"
  }' \
  localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL)

TTL_CODE=$(echo $RESPONSE | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
echo "Created expiring URL with code: $TTL_CODE"

echo "Resolving immediately (should work)..."
grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d "{
    \"code\": \"$TTL_CODE\",
    \"count_click\": false,
    \"client_ip\": \"127.0.0.1\"
  }" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL

echo "Waiting 6 seconds for TTL to expire..."
sleep 6

echo "Resolving after expiration (should fail with 404)..."
grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d "{
    \"code\": \"$TTL_CODE\",
    \"count_click\": false,
    \"client_ip\": \"127.0.0.1\"
  }" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL

# Test 8: Max Clicks
echo -e "\n✅ Test 8: Max Clicks (limit: 2)"
RESPONSE=$(grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d '{
    "long_url": "https://www.clicktest.com",
    "max_clicks": 2,
    "client_ip": "127.0.0.1"
  }' \
  localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL)

CLICK_CODE=$(echo $RESPONSE | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
echo "Created URL with max 2 clicks: $CLICK_CODE"

echo "Click 1..."
grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d "{
    \"code\": \"$CLICK_CODE\",
    \"count_click\": true,
    \"client_ip\": \"127.0.0.1\"
  }" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL | grep -o '"status":[0-9]*'

echo "Click 2..."
grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d "{
    \"code\": \"$CLICK_CODE\",
    \"count_click\": true,
    \"client_ip\": \"127.0.0.1\"
  }" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL | grep -o '"status":[0-9]*'

echo "Click 3 (should fail with 410)..."
grpcurl -plaintext \
  -proto $PROTO_FILE \
  -import-paths $PROTO_PATH \
  -d "{
    \"code\": \"$CLICK_CODE\",
    \"count_click\": true,
    \"client_ip\": \"127.0.0.1\"
  }" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL

echo -e "\n🎉 All tests completed!"
