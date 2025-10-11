# File: microservices_http/redirect_service/app.py
import os
import time
from fastapi import FastAPI, HTTPException,Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError,BaseModel
from common.lib.rate_limit import ShortenRequest, ShortenResponse, ResolveResponse
from common.lib.codegen import random_code
from common.lib.ttl import normalize_ttl
from persistence.redis_client import get_redis
from persistence.repositories import set_url, resolve_and_account, get_stats, remaining_clicks, ttl_remaining

app = FastAPI(title="redirect_service")
redis = get_redis()
GATEWAY_BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:8080")

@app.get("/healthz")
async def healthz():
    try:
        pong = await redis.ping()
        return {"status": "ok", "redis": pong}
    except Exception as e:
        return JSONResponse({"status": "degraded", "error": str(e)}, status_code=500)

@app.post("/shorten", response_model=ShortenResponse)
async def shorten(payload: ShortenRequest):
    ttl_sec = normalize_ttl(payload.ttl_sec)
    max_clicks = payload.max_clicks
    # generate code; allow rare collisions by retry
    for _ in range(5):
        code = random_code(7)
        key_exists = await redis.exists(f"url:{code}")
        if not key_exists:
            break
    else:
        raise HTTPException(500, "Failed to allocate short code")
    await set_url(redis, code, str(payload.long_url), ttl_sec, max_clicks)
    return ShortenResponse(code=code, short_url=f"{GATEWAY_BASE_URL}/{code}")

@app.get("/resolve/{code}", response_model=ResolveResponse)
async def resolve(code: str, count: bool = Query(default=True)):
    status, url = await resolve_and_account(redis, code, count_click=count)  # CHANGED
    if status == 404:
        raise HTTPException(404, "Not found or expired")
    if status == 410:
        raise HTTPException(410, "Link click limit exceeded")
    return ResolveResponse(long_url=url)

class StatsResponse(BaseModel):
    code: str
    total_clicks: int
    created_at: int
    expired: bool
    remaining_clicks: int | None = None
    ttl_remaining_sec: int | None = None
    created_at_iso: str | None = None

@app.get("/stats/{code}", response_model=StatsResponse)
async def stats(code: str):
    s = await get_stats(redis, code)
    if not s: raise HTTPException(404, "Code not found")
    rem = await remaining_clicks(redis, code)
    ttl = await ttl_remaining(redis, code)
    from datetime import datetime, timezone
    s["remaining_clicks"] = rem
    s["ttl_remaining_sec"] = ttl if ttl >= 0 else None
    s["created_at_iso"] = datetime.fromtimestamp(s["created_at"], tz=timezone.utc).isoformat()
    return StatsResponse(**s)
