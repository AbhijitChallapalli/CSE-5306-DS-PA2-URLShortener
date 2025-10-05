# File: persistence/redis_client.py
import os
from redis.asyncio import Redis

def get_redis() -> Redis:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(url, decode_responses=True)
