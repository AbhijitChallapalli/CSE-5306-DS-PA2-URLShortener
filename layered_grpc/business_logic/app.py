import os
import grpc
import secrets
import string
from concurrent import futures

import business_pb2
import business_pb2_grpc
import data_pb2
import data_pb2_grpc

ALPHABET = string.ascii_letters + string.digits

def random_code(length: int = 7) -> str:
    return ''.join(secrets.choice(ALPHABET) for _ in range(length))

def normalize_ttl(ttl_sec):
    if ttl_sec is None or ttl_sec <= 0:
        return None
    return max(1, int(ttl_sec))

class BusinessLogicServiceImpl(business_pb2_grpc.BusinessLogicServiceServicer):
    def __init__(self):
        data_service_addr = os.getenv("DATA_SERVICE_URL", "localhost:50053")
        self.data_channel = grpc.aio.insecure_channel(data_service_addr)
        self.data_stub = data_pb2_grpc.DataServiceStub(self.data_channel)
        
        self.gateway_base_url = os.getenv("GATEWAY_BASE_URL", "http://localhost:8080")
        self.default_rate_limit = int(os.getenv("RL_LIMIT_PER_MIN", "120"))
        self.default_rate_window = int(os.getenv("RL_WINDOW_SEC", "60"))
    
    async def CreateShortURL(self, request, context):
        try:
            rate_check = await self.data_stub.CheckRateLimit(
                data_pb2.CheckRateLimitRequest(
                    ip=request.client_ip,
                    limit=self.default_rate_limit,
                    window_sec=self.default_rate_window
                )
            )
            
            if not rate_check.allowed:
                return business_pb2.CreateShortURLResponse(
                    success=False,
                    code="",
                    short_url="",
                    error="Rate limit exceeded"
                )
            
            if not request.long_url or len(request.long_url) < 10:
                return business_pb2.CreateShortURLResponse(
                    success=False,
                    code="",
                    short_url="",
                    error="Invalid URL"
                )
            
            ttl_sec = None
            if request.HasField('ttl_sec'):
                ttl_sec = normalize_ttl(request.ttl_sec)
            
            code = None
            for _ in range(5):
                candidate = random_code(7)
                check_response = await self.data_stub.GetURL(
                    data_pb2.GetURLRequest(code=candidate)
                )
                if not check_response.found:
                    code = candidate
                    break
            
            if not code:
                return business_pb2.CreateShortURLResponse(
                    success=False,
                    code="",
                    short_url="",
                    error="Failed to generate unique code"
                )
            
            store_request = data_pb2.StoreURLRequest(
                code=code,
                long_url=request.long_url
            )
            if ttl_sec:
                store_request.ttl_sec = ttl_sec
            if request.HasField('max_clicks'):
                store_request.max_clicks = request.max_clicks
            
            store_response = await self.data_stub.StoreURL(store_request)
            
            if not store_response.success:
                return business_pb2.CreateShortURLResponse(
                    success=False,
                    code="",
                    short_url="",
                    error=store_response.error
                )
            
            short_url = f"{self.gateway_base_url}/{code}"
            return business_pb2.CreateShortURLResponse(
                success=True,
                code=code,
                short_url=short_url,
                error=""
            )
            
        except Exception as e:
            return business_pb2.CreateShortURLResponse(
                success=False,
                code="",
                short_url="",
                error=str(e)
            )
    
    async def ResolveShortURL(self, request, context):
        try:
            rate_check = await self.data_stub.CheckRateLimit(
                data_pb2.CheckRateLimitRequest(
                    ip=request.client_ip,
                    limit=self.default_rate_limit,
                    window_sec=self.default_rate_window
                )
            )
            
            if not rate_check.allowed:
                return business_pb2.ResolveShortURLResponse(
                    status=429,
                    long_url="",
                    error="Too Many Requests"
                )
            
            resolve_response = await self.data_stub.ResolveURL(
                data_pb2.ResolveURLRequest(
                    code=request.code,
                    count_click=request.count_click
                )
            )
            
            if resolve_response.status == 200 and request.count_click:
                try:
                    await self.data_stub.IncrementClick(
                        data_pb2.IncrementClickRequest(code=request.code)
                    )
                except:
                    pass
            
            error_msg = ""
            if resolve_response.status == 404:
                error_msg = "Not found or expired"
            elif resolve_response.status == 410:
                error_msg = "Link expired (max clicks reached)"
            
            return business_pb2.ResolveShortURLResponse(
                status=resolve_response.status,
                long_url=resolve_response.long_url,
                error=error_msg
            )
            
        except Exception as e:
            return business_pb2.ResolveShortURLResponse(
                status=500,
                long_url="",
                error=str(e)
            )
    
    async def GetTopLinks(self, request, context):
        try:
            data_response = await self.data_stub.GetTopLinks(
                data_pb2.GetTopLinksRequest(limit=request.limit)
            )
            
            links = [
                business_pb2.TopLink(
                    code=link.code,
                    clicks=link.clicks,
                    long_url=link.long_url
                )
                for link in data_response.links
            ]
            
            return business_pb2.GetTopLinksResponse(links=links)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return business_pb2.GetTopLinksResponse(links=[])
    
    async def CheckRateLimit(self, request, context):
        try:
            response = await self.data_stub.CheckRateLimit(
                data_pb2.CheckRateLimitRequest(
                    ip=request.ip,
                    limit=self.default_rate_limit,
                    window_sec=self.default_rate_window
                )
            )
            return business_pb2.CheckRateLimitResponse(
                allowed=response.allowed,
                remaining=response.remaining
            )
        except Exception as e:
            return business_pb2.CheckRateLimitResponse(
                allowed=False,
                remaining=0
            )
    
    async def HealthCheck(self, request, context):
        try:
            data_health = await self.data_stub.HealthCheck(
                data_pb2.HealthCheckRequest()
            )
            return business_pb2.HealthCheckResponse(
                status="ok" if data_health.status == "ok" else "degraded",
                data_service_status=data_health.status
            )
        except Exception as e:
            return business_pb2.HealthCheckResponse(
                status="error",
                data_service_status="unreachable"
            )

async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    business_pb2_grpc.add_BusinessLogicServiceServicer_to_server(
        BusinessLogicServiceImpl(), server
    )
    listen_addr = '[::]:50052'
    server.add_insecure_port(listen_addr)
    print(f"Business Logic Service listening on {listen_addr}")
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    import asyncio
    asyncio.run(serve())
