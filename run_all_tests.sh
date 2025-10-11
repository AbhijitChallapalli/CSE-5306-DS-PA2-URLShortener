#!/bin/bash

PROTO="layered_simple/src/proto/urlshortener.proto"
IMPORT="layered_simple/src/proto"

echo "=========================================="
echo "  LAYERED ARCHITECTURE - ALL TESTS"
echo "=========================================="

echo -e "\n[TEST 1] Health Check"
grpcurl -plaintext -proto $PROTO -import-path $IMPORT -d '{}' localhost:8081 urlshort.v1.URLShortenerService.HealthCheck

echo -e "\n[TEST 2] Create Short URL"
RESPONSE=$(grpcurl -plaintext -proto $PROTO -import-path $IMPORT -d '{"long_url": "https://www.google.com", "ttl_sec": 3600, "max_clicks": 10, "client_ip": "127.0.0.1"}' localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL)
echo "$RESPONSE"
CODE=$(echo $RESPONSE | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
echo "Created code: $CODE"

echo -e "\n[TEST 3] Resolve URL"
grpcurl -plaintext -proto $PROTO -import-path $IMPORT -d "{\"code\": \"$CODE\", \"count_click\": true, \"client_ip\": \"127.0.0.1\"}" localhost:8081 urlshort.v1.URLShortenerService.ResolveURL

echo -e "\n[TEST 4] Get Top Links"
grpcurl -plaintext -proto $PROTO -import-path $IMPORT -d '{"limit": 5}' localhost:8081 urlshort.v1.URLShortenerService.GetTopLinks

echo -e "\n[TEST 5] Get Statistics"
grpcurl -plaintext -proto $PROTO -import-path $IMPORT -d "{\"code\": \"$CODE\"}" localhost:8081 urlshort.v1.URLShortenerService.GetStats

echo -e "\n[TEST 6] TTL Test (5 second expiration)"
RESPONSE_TTL=$(grpcurl -plaintext -proto $PROTO -import-path $IMPORT -d '{"long_url": "https://www.expiretest.com", "ttl_sec": 5, "client_ip": "127.0.0.1"}' localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL)
CODE_TTL=$(echo $RESPONSE_TTL | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
echo "Created expiring code: $CODE_TTL"
echo "Resolving immediately..."
grpcurl -plaintext -proto $PROTO -import-path $IMPORT -d "{\"code\": \"$CODE_TTL\", \"count_click\": false, \"client_ip\": \"127.0.0.1\"}" localhost:8081 urlshort.v1.URLShortenerService.ResolveURL | head -3
echo "Waiting 6 seconds..."
sleep 6
echo "Resolving after expiration..."
grpcurl -plaintext -proto $PROTO -import-path $IMPORT -d "{\"code\": \"$CODE_TTL\", \"count_click\": false, \"client_ip\": \"127.0.0.1\"}" localhost:8081 urlshort.v1.URLShortenerService.ResolveURL

echo -e "\n[TEST 7] Max Clicks Test (limit: 2)"
RESPONSE_CLICK=$(grpcurl -plaintext -proto $PROTO -import-path $IMPORT -d '{"long_url": "https://www.clicktest.com", "max_clicks": 2, "client_ip": "127.0.0.1"}' localhost:8081 urlshort.v1.URLShortenerService.CreateShortURL)
CODE_CLICK=$(echo $RESPONSE_CLICK | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
echo "Created code: $CODE_CLICK"
echo "Click 1:"
grpcurl -plaintext -proto $PROTO -import-path $IMPORT -d "{\"code\": \"$CODE_CLICK\", \"count_click\": true, \"client_ip\": \"127.0.0.1\"}" localhost:8081 urlshort.v1.URLShortenerService.ResolveURL | grep status
echo "Click 2:"
grpcurl -plaintext -proto $PROTO -import-path $IMPORT -d "{\"code\": \"$CODE_CLICK\", \"count_click\": true, \"client_ip\": \"127.0.0.1\"}" localhost:8081 urlshort.v1.URLShortenerService.ResolveURL | grep status
echo "Click 3 (should fail):"
grpcurl -plaintext -proto $PROTO -import-path $IMPORT -d "{\"code\": \"$CODE_CLICK\", \"count_click\": true, \"client_ip\": \"127.0.0.1\"}" localhost:8081 urlshort.v1.URLShortenerService.ResolveURL

echo -e "\n=========================================="
echo "  ✅ ALL TESTS COMPLETED!"
echo "=========================================="
