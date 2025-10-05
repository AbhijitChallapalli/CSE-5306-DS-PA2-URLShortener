# File: microservices_http/analytics_service/app.py
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from persistence.redis_client import get_redis
from persistence.repositories import zset_top, zset_increment, get_long_url

app = FastAPI(title="analytics_service")
redis = get_redis()

@app.get("/healthz")
async def healthz():
    try:
        pong = await redis.ping()
        return {"status": "ok", "redis": pong}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

@app.post("/increment/{code}", status_code=204)
async def increment(code: str):
    # Do not validate existence strictly to keep path non-blocking; optional:
    exists = await get_long_url(redis, code)
    if not exists:
        raise HTTPException(404, "code not found")
    await zset_increment(redis, code)
    return

@app.get("/top")
async def top(limit: int = 10) -> List[Dict]:
    data = await zset_top(redis, limit)
    result = []
    for code, clicks in data:
        url = await get_long_url(redis, code)
        if url:
            result.append({"code": code, "clicks": clicks, "long_url": url})
    return result
