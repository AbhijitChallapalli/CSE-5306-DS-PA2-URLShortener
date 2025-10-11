#!/bin/bash

PROTO="layered_simple/src/proto/urlshortener.proto"
IMPORT="layered_simple/src/proto"

echo "=========================================="
echo "  LAYERED ARCHITECTURE - ALL TESTS"
echo "=========================================="

# Test 1: Health Check
echo -e "\n[TEST 1] Health Check"
grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
  -d '{}' localhost:8081 urlshort.v1.URLShortenerService.HealthCheck

# Test 2: Create Short URL
echo -e "\n[TEST 2] Create Short URL"
RESPONSE=$(grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
  -d '{"long_url": "https://www.google.com", "ttl_sec": 3600, "max_clicks": 10, "client_ip": "127.0.0.1"}' \
  localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL)

echo "$RESPONSE"

# Better code extraction using jq (or fallback to grep)
if command -v jq &> /dev/null; then
  CODE=$(echo "$RESPONSE" | jq -r '.code')
else
  # Fallback: Use sed for more reliable extraction
  CODE=$(echo "$RESPONSE" | sed -n 's/.*"code": *"\([^"]*\)".*/\1/p')
fi

echo "Extracted code: '$CODE'"

# Only proceed if we got a code
if [ -z "$CODE" ] || [ "$CODE" = "null" ]; then
  echo "ERROR: Failed to extract code. Response was:"
  echo "$RESPONSE"
  exit 1
fi

# Test 3: Resolve URL
echo -e "\n[TEST 3] Resolve URL (code: $CODE)"
grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
  -d "{\"code\": \"$CODE\", \"count_click\": true, \"client_ip\": \"127.0.0.1\"}" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL

# Test 4: Create more URLs and resolve them to generate clicks
echo -e "\n[TEST 4] Creating and resolving more URLs"
for URL in "https://www.facebook.com" "https://www.github.com" "https://www.twitter.com"; do
  RESP=$(grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
    -d "{\"long_url\": \"$URL\", \"client_ip\": \"127.0.0.1\"}" \
    localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL)
  
  if command -v jq &> /dev/null; then
    C=$(echo "$RESP" | jq -r '.code')
  else
    C=$(echo "$RESP" | sed -n 's/.*"code": *"\([^"]*\)".*/\1/p')
  fi
  
  echo "Created: $URL -> $C"
  
  # Resolve it to generate a click
  grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
    -d "{\"code\": \"$C\", \"count_click\": true, \"client_ip\": \"127.0.0.1\"}" \
    localhost:8081 urlshort.v1.URLShortenerService.ResolveURL > /dev/null 2>&1
done

# Resolve original code again
grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
  -d "{\"code\": \"$CODE\", \"count_click\": true, \"client_ip\": \"127.0.0.1\"}" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL > /dev/null 2>&1

# Test 5: Get Top Links
echo -e "\n[TEST 5] Get Top Links"
grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
  -d '{"limit": 5}' localhost:8081 urlshort.v1.URLShortenerService.GetTopLinks

# Test 6: Get Statistics
echo -e "\n[TEST 6] Get Statistics (code: $CODE)"
grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
  -d "{\"code\": \"$CODE\"}" \
  localhost:8081 urlshort.v1.URLShortenerService.GetStats

# Test 7: TTL Expiration
echo -e "\n[TEST 7] TTL Expiration Test (5 seconds)"
RESPONSE_TTL=$(grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
  -d '{"long_url": "https://www.expiretest.com", "ttl_sec": 5, "client_ip": "127.0.0.1"}' \
  localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL)

if command -v jq &> /dev/null; then
  CODE_TTL=$(echo "$RESPONSE_TTL" | jq -r '.code')
else
  CODE_TTL=$(echo "$RESPONSE_TTL" | sed -n 's/.*"code": *"\([^"]*\)".*/\1/p')
fi

echo "Created expiring code: $CODE_TTL"

echo "Resolving immediately (should work)..."
grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
  -d "{\"code\": \"$CODE_TTL\", \"count_click\": false, \"client_ip\": \"127.0.0.1\"}" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL | grep -E "(status|longUrl)"

echo "Waiting 6 seconds for expiration..."
sleep 6

echo "Resolving after expiration (should return 404)..."
grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
  -d "{\"code\": \"$CODE_TTL\", \"count_click\": false, \"client_ip\": \"127.0.0.1\"}" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL

# Test 8: Max Clicks
echo -e "\n[TEST 8] Max Clicks Test (limit: 2)"
RESPONSE_CLICK=$(grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
  -d '{"long_url": "https://www.clicktest.com", "max_clicks": 2, "client_ip": "127.0.0.1"}' \
  localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL)

if command -v jq &> /dev/null; then
  CODE_CLICK=$(echo "$RESPONSE_CLICK" | jq -r '.code')
else
  CODE_CLICK=$(echo "$RESPONSE_CLICK" | sed -n 's/.*"code": *"\([^"]*\)".*/\1/p')
fi

echo "Created code with max 2 clicks: $CODE_CLICK"

echo "Click 1 (should return 200):"
grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
  -d "{\"code\": \"$CODE_CLICK\", \"count_click\": true, \"client_ip\": \"127.0.0.1\"}" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL | grep status

echo "Click 2 (should return 200):"
grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
  -d "{\"code\": \"$CODE_CLICK\", \"count_click\": true, \"client_ip\": \"127.0.0.1\"}" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL | grep status

echo "Click 3 (should return 410 - expired):"
grpcurl -plaintext -proto $PROTO -import-path $IMPORT \
  -d "{\"code\": \"$CODE_CLICK\", \"count_click\": true, \"client_ip\": \"127.0.0.1\"}" \
  localhost:8081 urlshort.v1.URLShortenerService.ResolveURL

echo -e "\n=========================================="
echo "  ✅ ALL TESTS COMPLETED!"
echo "=========================================="
