# Layer 3: Repository / Data Access Layer
import time
from typing import Optional, List, Tuple
from redis.asyncio import Redis

class RedisRepository:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.lua_resolve = """
        local url = redis.call('GET', KEYS[1])
        if not url then
          return {404, ""}
        end
        if tonumber(ARGV[1]) == 1 then
          local rem = redis.call('GET', KEYS[2])
          if rem then
            rem = tonumber(rem) - 1
            if rem < 0 then
              redis.call('SET', KEYS[2], 0)
              return {410, ""}
            else
              redis.call('SET', KEYS[2], tostring(rem))
            end
          end
        end
        return {200, url}
        """
    
    async def store_url(self, code: str, long_url: str, 
                       ttl_sec: Optional[int] = None, 
                       max_clicks: Optional[int] = None) -> bool:
        try:
            url_key = f"url:{code}"
            await self.redis.set(url_key, long_url)
            if ttl_sec:
                await self.redis.expire(url_key, ttl_sec)
            if max_clicks:
                await self.redis.set(f"rem_clicks:{code}", max_clicks)
            await self.redis.hset(f"meta:{code}", mapping={
                "created_at": int(time.time()),
                "max_clicks": max_clicks or 0
            })
            return True
        except Exception as e:
            print(f"Error storing URL: {e}")
            return False
    
    async def get_url(self, code: str) -> Optional[str]:
        try:
            return await self.redis.get(f"url:{code}")
        except Exception:
            return None
    
    async def resolve_url(self, code: str, count_click: bool = True) -> Tuple[int, str]:
        try:
            sha = await self.redis.script_load(self.lua_resolve)
            status, url = await self.redis.evalsha(
                sha, 2, f"url:{code}", f"rem_clicks:{code}",
                1 if count_click else 0
            )
            return int(status), url
        except Exception as e:
            print(f"Error resolving URL: {e}")
            return 500, ""
    
    async def increment_click(self, code: str) -> bool:
        try:
            await self.redis.zincrby("zset:clicks", 1, code)
            await self.redis.hset(f"meta:{code}", "last_click", int(time.time()))
            return True
        except Exception:
            return False
    
    async def get_top_links(self, limit: int = 10) -> List[Tuple[str, int, str]]:
        try:
            members = await self.redis.zrevrange("zset:clicks", 0, limit - 1, withscores=True)
            result = []
            for code, score in members:
                url = await self.get_url(code)
                if url:
                    result.append((code, int(score), url))
            return result
        except Exception:
            return []
    
    async def check_rate_limit(self, ip: str, limit: int, window_sec: int) -> Tuple[bool, int]:
        try:
            key = f"ratelimit:{ip}"
            now = int(time.time())
            window_start = now - window_sec
            await self.redis.zremrangebyscore(key, 0, window_start)
            current_count = await self.redis.zcard(key)
            if current_count >= limit:
                return False, 0
            await self.redis.zadd(key, {str(now): now})
            await self.redis.expire(key, window_sec)
            return True, limit - current_count - 1
        except Exception:
            return False, 0
    
    async def get_stats(self, code: str) -> Optional[dict]:
        try:
            meta = await self.redis.hgetall(f"meta:{code}")
            clicks = await self.redis.zscore("zset:clicks", code)
            if not meta:
                return None
            return {
                "created_at": int(meta.get("created_at", 0)),
                "max_clicks": int(meta.get("max_clicks", 0)),
                "last_click": int(meta.get("last_click", 0)),
                "total_clicks": int(clicks) if clicks else 0
            }
        except Exception:
            return None
    
    async def ping(self) -> bool:
        try:
            return await self.redis.ping()
        except Exception:
            return False
