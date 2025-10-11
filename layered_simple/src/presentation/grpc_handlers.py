# Layer 1: Presentation / gRPC Handlers Layer
import grpc
from service.url_service import URLShortenerService
import urlshortener_pb2
import urlshortener_pb2_grpc

class URLShortenerServicer(urlshortener_pb2_grpc.URLShortenerServiceServicer):
    def __init__(self, service: URLShortenerService):
        self.service = service
    
    async def CreateShortURL(self, request, context):
        ttl_sec = request.ttl_sec if request.HasField('ttl_sec') else None
        max_clicks = request.max_clicks if request.HasField('max_clicks') else None
        
        success, code, short_url, error = await self.service.create_short_url(
            long_url=request.long_url,
            client_ip=request.client_ip,
            ttl_sec=ttl_sec,
            max_clicks=max_clicks
        )
        
        return urlshortener_pb2.CreateShortURLResponse(
            success=success, code=code, short_url=short_url, error=error
        )
    
    async def ResolveURL(self, request, context):
        status, long_url, error = await self.service.resolve_url(
            code=request.code,
            client_ip=request.client_ip,
            count_click=request.count_click
        )
        
        return urlshortener_pb2.ResolveURLResponse(
            status=status, long_url=long_url, error=error
        )
    
    async def GetTopLinks(self, request, context):
        links = await self.service.get_top_links(limit=request.limit)
        
        grpc_links = [
            urlshortener_pb2.LinkStats(
                code=link["code"],
                clicks=link["clicks"],
                long_url=link["long_url"]
            )
            for link in links
        ]
        
        return urlshortener_pb2.GetTopLinksResponse(links=grpc_links)
    
    async def GetStats(self, request, context):
        stats = await self.service.get_stats(code=request.code)
        
        if not stats:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Code not found")
            return urlshortener_pb2.GetStatsResponse()
        
        return urlshortener_pb2.GetStatsResponse(
            code=stats["code"],
            total_clicks=stats["total_clicks"],
            created_at=stats["created_at"],
            expired=stats["expired"]
        )
    
    async def HealthCheck(self, request, context):
        status, redis_ok = await self.service.health_check()
        return urlshortener_pb2.HealthCheckResponse(status=status, redis_ok=redis_ok)
