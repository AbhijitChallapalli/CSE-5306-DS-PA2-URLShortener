import os
import time
import grpc
from concurrent import futures
import redis.asyncio as redis

import data_pb2
import data_pb2_grpc

class DataServiceImpl(data_pb2_grpc.DataServiceServicer):
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.from_url(redis_url, decode_responses=True)
        
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
        
    async def StoreURL(self, request, context):
        try:
            url_key = f"url:{request.code}"
            await self.redis.set(url_key, request.long_url)
            
            if request.HasField('ttl_sec'):
                await self.redis.expire(url_key, request.ttl_sec)
            
            if request.HasField('max_clicks'):
                remain_key = f"rem_clicks:{request.code}"
                await self.redis.set(remain_key, request.max_clicks)
            
            return data_pb2.StoreURLResponse(success=True, error="")
        except Exception as e:
            return data_pb2.StoreURLResponse(success=False, error=str(e))
    
    async def GetURL(self, request, context):
        try:
            url_key = f"url:{request.code}"
            long_url = await self.redis.get(url_key)
            
            if long_url:
                return data_pb2.GetURLResponse(found=True, long_url=long_url)
            else:
                return data_pb2.GetURLResponse(found=False, long_url="")
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return data_pb2.GetURLResponse(found=False, long_url="")
    
    async def ResolveURL(self, request, context):
        try:
            sha = await self.redis.script_load(self.lua_resolve)
            url_key = f"url:{request.code}"
            remain_key = f"rem_clicks:{request.code}"
            
            status, url = await self.redis.evalsha(
                sha, 2, url_key, remain_key,
                1 if request.count_click else 0
            )
            
            return data_pb2.ResolveURLResponse(
                status=int(status),
                long_url=url
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return data_pb2.ResolveURLResponse(status=500, long_url="")
    
    async def IncrementClick(self, request, context):
        try:
            await self.redis.zincrby("zset:clicks", 1, request.code)
            return data_pb2.IncrementClickResponse(success=True)
        except Exception as e:
            return data_pb2.IncrementClickResponse(success=False)
    
    async def GetTopLinks(self, request, context):
        try:
            members = await self.redis.zrevrange(
                "zset:clicks", 0, request.limit - 1, withscores=True
            )
            
            links = []
            for code, score in members:
                url_key = f"url:{code}"
                long_url = await self.redis.get(url_key)
                if long_url:
                    links.append(data_pb2.TopLink(
                        code=code,
                        clicks=int(score),
                        long_url=long_url
                    ))
            
            return data_pb2.GetTopLinksResponse(links=links)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return data_pb2.GetTopLinksResponse(links=[])
    
    async def CheckRateLimit(self, request, context):
        try:
            key = f"ratelimit:{request.ip}"
            now = int(time.time())
            window_start = now - request.window_sec
            
            await self.redis.zremrangebyscore(key, 0, window_start)
            current_count = await self.redis.zcard(key)
            
            if current_count >= request.limit:
                return data_pb2.CheckRateLimitResponse(
                    allowed=False,
                    remaining=0
                )
            
            await self.redis.zadd(key, {str(now): now})
            await self.redis.expire(key, request.window_sec)
            
            remaining = request.limit - current_count - 1
            return data_pb2.CheckRateLimitResponse(
                allowed=True,
                remaining=remaining
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return data_pb2.CheckRateLimitResponse(allowed=False, remaining=0)
    
    async def HealthCheck(self, request, context):
        try:
            pong = await self.redis.ping()
            return data_pb2.HealthCheckResponse(
                status="ok" if pong else "degraded",
                redis_ok=pong
            )
        except Exception as e:
            return data_pb2.HealthCheckResponse(
                status="error",
                redis_ok=False
            )

async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    data_pb2_grpc.add_DataServiceServicer_to_server(
        DataServiceImpl(), server
    )
    listen_addr = '[::]:50053'
    server.add_insecure_port(listen_addr)
    print(f"Data Service listening on {listen_addr}")
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    import asyncio
    asyncio.run(serve())
