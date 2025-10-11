# File: microservices_http/api_gateway/app.py
import os
import httpx
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import RedirectResponse
from common.lib.rate_limit import ShortenRequest, ShortenResponse

app = FastAPI(title="api_gateway")

REDIRECT_URL   = os.getenv("REDIRECT_URL",   "http://redirect:8001")
ANALYTICS_URL  = os.getenv("ANALYTICS_URL",  "http://analytics:8002")
RATELIMIT_URL  = os.getenv("RATELIMIT_URL",  "http://ratelimit:8003")

client = httpx.AsyncClient(timeout=5.0)

def client_ip(req: Request) -> str:
    fwd = req.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return req.client.host if req.client else "unknown"

@app.get("/healthz")
async def healthz():
    # Best-effort fan-out checks
    try:
        r = await client.get(f"{REDIRECT_URL}/healthz")
        a = await client.get(f"{ANALYTICS_URL}/healthz")
        t = await client.get(f"{RATELIMIT_URL}/healthz")
        return {"gateway": "ok", "redirect": r.json(), "analytics": a.json(), "ratelimit": t.json()}
    except Exception as e:
        return {"gateway": "degraded", "error": str(e)}

@app.post("/shorten", response_model=ShortenResponse)
async def shorten(req: Request, payload: ShortenRequest):
    ip = client_ip(req)
    _ = await client.get(f"{RATELIMIT_URL}/check", params={"ip": ip})
    data = payload.model_dump(mode="json")          # <-- FIX
    r = await client.post(f"{REDIRECT_URL}/shorten", json=data)
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return ShortenResponse(**r.json())

@app.api_route("/{code}", methods=["GET", "HEAD"])
async def redirect_or_head(req: Request, code: str):
    ip = client_ip(req)

    # rate limit both GET and HEAD
    rl = await client.get(f"{RATELIMIT_URL}/check", params={"ip": ip})
    if rl.status_code == 429:
        raise HTTPException(429, "Too Many Requests")

    # HEAD should NOT consume click -> count=false
    count = "false" if req.method == "HEAD" else "true"
    r = await client.get(f"{REDIRECT_URL}/resolve/{code}", params={"count": count})

    if r.status_code == 404:
        raise HTTPException(404, "Link not found")
    if r.status_code == 410:
        raise HTTPException(410, "Link expired")

    long_url = r.json()["long_url"]

    # Only GET increments analytics
    if req.method == "GET":
        try:
            await client.post(f"{ANALYTICS_URL}/increment/{code}")
        except:
            pass

    # Return 301; for HEAD, empty body with Location header
    if req.method == "HEAD":
        return Response(status_code=301, headers={"Location": long_url})
    return RedirectResponse(url=long_url, status_code=301)

@app.get("/analytics/top")
async def top(limit: int = 10):
    r = await client.get(f"{ANALYTICS_URL}/top", params={"limit": limit})
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.get("/stats/{code}")
async def stats(code: str):
    r = await client.get(f"{REDIRECT_URL}/stats/{code}")
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.get("/api/resolve")
async def api_resolve(code: str, count: bool = True):
    r = await client.get(f"{REDIRECT_URL}/resolve/{code}", params={"count": "true" if count else "false"})
    if r.status_code >= 400: raise HTTPException(r.status_code, r.text)
    return r.json()  # {"long_url": "..."}
