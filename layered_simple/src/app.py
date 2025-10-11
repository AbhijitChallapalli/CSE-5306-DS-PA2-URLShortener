# Main application - wires up the 3 layers
import os
import asyncio
import grpc
from concurrent import futures
from redis.asyncio import Redis

from repository.redis_repo import RedisRepository
from service.url_service import URLShortenerService
from presentation.grpc_handlers import URLShortenerServicer
import urlshortener_pb2_grpc

async def serve():
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    grpc_port = os.getenv("GRPC_PORT", "50051")
    
    print("=" * 60)
    print("Starting Layered URL Shortener Service")
    print("=" * 60)
    print(f"Redis URL: {redis_url}")
    print(f"gRPC Port: {grpc_port}")
    
    redis_client = Redis.from_url(redis_url, decode_responses=True)
    repository = RedisRepository(redis_client)
    
    try:
        await repository.ping()
        print("✓ Redis connection: OK")
    except Exception as e:
        print(f"✗ Redis connection: FAILED - {e}")
        return
    
    service = URLShortenerService(repository)
    print("✓ Service Layer initialized")
    
    servicer = URLShortenerServicer(service)
    print("✓ Presentation Layer initialized")
    
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    urlshortener_pb2_grpc.add_URLShortenerServiceServicer_to_server(servicer, server)
    
    listen_addr = f'[::]:{grpc_port}'
    server.add_insecure_port(listen_addr)
    
    print(f"✓ gRPC server listening on {listen_addr}")
    print("=" * 60)
    print("Architecture: Single Container, 3 Layers")
    print("  Layer 1 → Layer 2 → Layer 3 → Redis")
    print("  (function calls only, no internal gRPC)")
    print("=" * 60)
    
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down...")
        await server.stop(grace=5)
        await redis_client.close()

if __name__ == '__main__':
    asyncio.run(serve())
