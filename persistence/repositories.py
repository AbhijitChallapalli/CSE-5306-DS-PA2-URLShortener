# # File: persistence/repositories.py
# from typing import Optional, List, Tuple, Dict, Any
# from redis.asyncio import Redis

# URL_KEY = "url:{code}"          # string long_url
# META_KEY = "urlmeta:{code}"     # hash: created_at, max_clicks, ...
# REMAIN_KEY = "rem_clicks:{code}"# string int remaining
# ZSET_CLICKS = "zset:clicks"     # sorted set: code -> clicks score

# LUA_DECR_AND_FETCH = """
# -- KEYS[1]=url_key, KEYS[2]=remain_key
# -- ARGV[1]=increment_clicks (0/1), ARGV[2]=zset name, ARGV[3]=code
# local url = redis.call('GET', KEYS[1])
# if not url then
#   return {404, ""}  -- not found or TTL expired
# end
# local rk = KEYS[2]
# local rem = redis.call('GET', rk)
# if rem then
#   rem = tonumber(rem) - 1
#   if rem < 0 then
#     redis.call('SET', rk, 0)
#     return {410, ""} -- gone by max_clicks
#   else
#     redis.call('SET', rk, tostring(rem))
#   end
# end
# if tonumber(ARGV[1]) == 1 then
#   redis.call('ZINCRBY', ARGV[2], 1, ARGV[3])
# end
# return {200, url}
# """

# async def set_url(redis: Redis, code: str, long_url: str,
#                   ttl_sec: Optional[int], max_clicks: Optional[int]) -> None:
#     url_key = URL_KEY.format(code=code)
#     await redis.set(url_key, long_url)
#     if ttl_sec:
#         await redis.expire(url_key, ttl_sec)
#     if max_clicks:
#         await redis.set(REMAIN_KEY.format(code=code), int(max_clicks))

# async def get_long_url(redis: Redis, code: str) -> Optional[str]:
#     return await redis.get(URL_KEY.format(code=code))

# async def resolve_and_account(redis: Redis, code: str, increment_clicks: bool = False) -> Tuple[int, str]:
#     """Atomically: check exists, enforce click cap, optionally bump ZSET."""
#     sha = await redis.script_load(LUA_DECR_AND_FETCH)
#     url_key = URL_KEY.format(code=code)
#     remain_key = REMAIN_KEY.format(code=code)
#     status, url = await redis.evalsha(
#         sha, 2, url_key, remain_key,
#         1 if increment_clicks else 0, ZSET_CLICKS, code
#     )
#     return int(status), url

# async def zset_top(redis: Redis, limit: int = 10) -> List[Tuple[str, int]]:
#     members = await redis.zrevrange(ZSET_CLICKS, 0, limit - 1, withscores=True)
#     return [(code, int(score)) for code, score in members]

# async def zset_increment(redis: Redis, code: str) -> None:
#     await redis.zincrby(ZSET_CLICKS, 1, code)


# File: persistence/repositories.py
from typing import Optional, List, Tuple
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
