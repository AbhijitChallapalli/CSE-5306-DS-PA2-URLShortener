import os
import grpc
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

import business_pb2
import business_pb2_grpc

app = FastAPI(title="api_gateway_layered")

business_service_addr = os.getenv("BUSINESS_SERVICE_URL", "localhost:50052")
channel = grpc.aio.insecure_channel(business_service_addr)
business_stub = business_pb2_grpc.BusinessLogicServiceStub(channel)

class ShortenRequest(BaseModel):
    long_url: HttpUrl
    ttl_sec: Optional[int] = Field(default=None, ge=1)
    max_clicks: Optional[int] = Field(default=None, ge=1)

class ShortenResponse(BaseModel):
    code: str
    short_url: str

def client_ip(req: Request) -> str:
    fwd = req.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return req.client.host if req.client else "unknown"

@app.get("/healthz")
async def healthz():
    try:
        response = await business_stub.HealthCheck(
            business_pb2.HealthCheckRequest()
        )
        return {
            "gateway": "ok",
            "business_logic": response.status,
            "data_service": response.data_service_status
        }
    except Exception as e:
        return {"gateway": "degraded", "error": str(e)}

@app.post("/shorten", response_model=ShortenResponse)
async def shorten(req: Request, payload: ShortenRequest):
    ip = client_ip(req)
    
    grpc_request = business_pb2.CreateShortURLRequest(
        long_url=str(payload.long_url),
        client_ip=ip
    )
    
    if payload.ttl_sec:
        grpc_request.ttl_sec = payload.ttl_sec
    if payload.max_clicks:
        grpc_request.max_clicks = payload.max_clicks
    
    try:
        response = await business_stub.CreateShortURL(grpc_request)
        
        if not response.success:
            if "rate limit" in response.error.lower():
                raise HTTPException(429, response.error)
            raise HTTPException(400, response.error)
        
        return ShortenResponse(
            code=response.code,
            short_url=response.short_url
        )
    except grpc.RpcError as e:
        raise HTTPException(500, f"gRPC error: {e.details()}")

@app.api_route("/{code}", methods=["GET", "HEAD"])
async def redirect_or_head(req: Request, code: str):
    ip = client_ip(req)
    count_click = (req.method == "GET")
    
    grpc_request = business_pb2.ResolveShortURLRequest(
        code=code,
        count_click=count_click,
        client_ip=ip
    )
    
    try:
        response = await business_stub.ResolveShortURL(grpc_request)
        
        if response.status == 404:
            raise HTTPException(404, response.error)
        elif response.status == 410:
            raise HTTPException(410, response.error)
        elif response.status == 429:
            raise HTTPException(429, response.error)
        elif response.status != 200:
            raise HTTPException(500, "Internal server error")
        
        long_url = response.long_url
        
        if req.method == "HEAD":
            return Response(status_code=301, headers={"Location": long_url})
        return RedirectResponse(url=long_url, status_code=301)
        
    except grpc.RpcError as e:
        raise HTTPException(500, f"gRPC error: {e.details()}")

@app.get("/analytics/top")
async def top(limit: int = 10):
    grpc_request = business_pb2.GetTopLinksRequest(limit=limit)
    
    try:
        response = await business_stub.GetTopLinks(grpc_request)
        
        return [
            {
                "code": link.code,
                "clicks": link.clicks,
                "long_url": link.long_url
            }
            for link in response.links
        ]
    except grpc.RpcError as e:
        raise HTTPException(500, f"gRPC error: {e.details()}")
