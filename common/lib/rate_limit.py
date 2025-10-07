# File: common/lib/rate_limit.py
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from redis.asyncio import Redis
import time

# Pydantic models for HTTP API
class ShortenRequest(BaseModel):
    long_url: HttpUrl
    ttl_sec: Optional[int] = Field(default=None, ge=1)
    max_clicks: Optional[int] = Field(default=None, ge=1)

class ShortenResponse(BaseModel):
    code: str
    short_url: str

class ResolveResponse(BaseModel):
    long_url: str

# Rate limiting function
async def check_and_consume(redis: Redis, ip: str, limit: int, window_sec: int) -> tuple[bool, int]:
    """
    Check and consume rate limit using sliding window.
    Returns (allowed, remaining_count)
    """
    key = f"ratelimit:{ip}"
    now = int(time.time())
    window_start = now - window_sec
    
    # Remove old entries
    await redis.zremrangebyscore(key, 0, window_start)
    
    # Count current requests
    current_count = await redis.zcard(key)
    
    if current_count >= limit:
        return False, 0
    
    # Add current request
    await redis.zadd(key, {str(now): now})
    await redis.expire(key, window_sec)
    
    remaining = limit - current_count - 1
    return True, remaining
