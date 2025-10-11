# Analytics Worker - Background processor
import os
import asyncio
import time
from redis.asyncio import Redis

async def analytics_worker():
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    interval = int(os.getenv("WORKER_INTERVAL", "10"))
    
    redis = Redis.from_url(redis_url, decode_responses=True)
    
    print("Analytics Worker Started")
    print(f"Interval: {interval}s")
    
    iteration = 0
    
    while True:
        try:
            iteration += 1
            print(f"[{time.strftime('%H:%M:%S')}] Iteration {iteration}")
            
            total_links = 0
            cursor = 0
            while True:
                cursor, keys = await redis.scan(cursor, match="url:*", count=100)
                total_links += len(keys)
                if cursor == 0:
                    break
            
            top = await redis.zrevrange("zset:clicks", 0, 0, withscores=True)
            top_code = top[0][0] if top else "none"
            top_clicks = int(top[0][1]) if top else 0
            
            await redis.hset("stats:global", mapping={
                "total_links": total_links,
                "top_code": top_code,
                "top_clicks": top_clicks,
                "last_update": int(time.time())
            })
            
            print(f"  Total links: {total_links}, Top: {top_code} ({top_clicks} clicks)")
            
            await asyncio.sleep(interval)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(interval)
    
    await redis.close()

if __name__ == '__main__':
    asyncio.run(analytics_worker())
