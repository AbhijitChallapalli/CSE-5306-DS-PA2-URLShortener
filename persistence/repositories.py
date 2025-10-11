from typing import Optional, Tuple, List, Dict, Any
from redis.asyncio import Redis

URL_KEY = "url:{code}"
REMAIN_KEY = "rem_clicks:{code}"
ZSET_CLICKS = "zset:clicks"  # (still used by analytics_service)

# NEW: only decrement remaining clicks if count_click==1
LUA_RESOLVE = """
-- KEYS[1]=url_key, KEYS[2]=remain_key
-- ARGV[1]=count_click (0/1)
local url = redis.call('GET', KEYS[1])
if not url then
  return {404, ""}  -- not found or TTL expired
end
if tonumber(ARGV[1]) == 1 then
  local rem = redis.call('GET', KEYS[2])
  if rem then
    rem = tonumber(rem) - 1
    if rem < 0 then
      redis.call('SET', KEYS[2], 0)
      return {410, ""} -- gone by max_clicks
    else
      redis.call('SET', KEYS[2], tostring(rem))
    end
  end
end
return {200, url}
"""

async def set_url(redis: Redis, code: str, long_url: str,
                  ttl_sec: Optional[int], max_clicks: Optional[int]) -> None:
    url_key = URL_KEY.format(code=code)
    await redis.set(url_key, long_url)
    if ttl_sec:
        await redis.expire(url_key, ttl_sec)
    if max_clicks:
        await redis.set(REMAIN_KEY.format(code=code), int(max_clicks))

async def get_long_url(redis: Redis, code: str) -> Optional[str]:
    return await redis.get(URL_KEY.format(code=code))

# CHANGED: now takes count_click (True for GET, False for HEAD)
async def resolve_and_account(redis: Redis, code: str, count_click: bool = True) -> Tuple[int, str]:
    sha = await redis.script_load(LUA_RESOLVE)
    url_key = URL_KEY.format(code=code)
    remain_key = REMAIN_KEY.format(code=code)
    status, url = await redis.evalsha(
        sha, 2, url_key, remain_key,
        1 if count_click else 0
    )
    return int(status), url

async def zset_top(redis: Redis, limit: int = 10) -> List[Tuple[str, int]]:
    members = await redis.zrevrange(ZSET_CLICKS, 0, limit - 1, withscores=True)
    return [(code, int(score)) for code, score in members]

async def zset_increment(redis: Redis, code: str) -> None:
    await redis.zincrby(ZSET_CLICKS, 1, code)


async def get_stats(redis, code: str) -> Optional[Dict[str, Any]]:
    meta = await redis.hgetall(f"meta:{code}")
    if not meta:
        return None
    clicks = await redis.zscore("zset:clicks", code)
    url = await redis.get(f"url:{code}")            # None if TTL expired / deleted
    return {
        "code": code,
        "total_clicks": int(clicks) if clicks else 0,
        "created_at": int(meta.get("created_at", 0)),
        "expired": url is None
    }


async def remaining_clicks(redis, code: str):
    v = await redis.get(f"rem_clicks:{code}")
    return int(v) if v is not None else None

async def ttl_remaining(redis, code: str):
    return await redis.ttl(f"url:{code}")  # -2 missing, -1 no expire, >=0 seconds
