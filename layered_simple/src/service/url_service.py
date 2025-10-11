# Layer 2: Service / Business Logic Layer
import os
import secrets
import string
from typing import Optional, Tuple, List
from repository.redis_repo import RedisRepository

class URLShortenerService:
    ALPHABET = string.ascii_letters + string.digits
    
    def __init__(self, repository: RedisRepository):
        self.repo = repository
        self.gateway_base_url = os.getenv("GATEWAY_BASE_URL", "http://localhost:8081")
        self.rate_limit = int(os.getenv("RL_LIMIT_PER_MIN", "120"))
        self.rate_window = int(os.getenv("RL_WINDOW_SEC", "60"))
    
    def _generate_code(self, length: int = 7) -> str:
        return ''.join(secrets.choice(self.ALPHABET) for _ in range(length))
    
    def _normalize_ttl(self, ttl_sec: Optional[int]) -> Optional[int]:
        if ttl_sec is None or ttl_sec <= 0:
            return None
        return max(1, int(ttl_sec))
    
    def _validate_url(self, url: str) -> Tuple[bool, str]:
        if not url or len(url) < 10:
            return False, "URL too short"
        if not url.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https://"
        if len(url) > 2048:
            return False, "URL too long (max 2048 chars)"
        return True, ""
    
    async def create_short_url(self, long_url: str, client_ip: str,
                              ttl_sec: Optional[int] = None,
                              max_clicks: Optional[int] = None) -> Tuple[bool, str, str, str]:
        allowed, remaining = await self.repo.check_rate_limit(
            client_ip, self.rate_limit, self.rate_window
        )
        if not allowed:
            return False, "", "", "Rate limit exceeded"
        
        valid, error = self._validate_url(long_url)
        if not valid:
            return False, "", "", error
        
        ttl_sec = self._normalize_ttl(ttl_sec)
        
        code = None
        for _ in range(5):
            candidate = self._generate_code(7)
            existing = await self.repo.get_url(candidate)
            if not existing:
                code = candidate
                break
        
        if not code:
            return False, "", "", "Failed to generate unique code"
        
        success = await self.repo.store_url(code, long_url, ttl_sec, max_clicks)
        if not success:
            return False, "", "", "Failed to store URL"
        
        short_url = f"{self.gateway_base_url}/{code}"
        return True, code, short_url, ""
    
    async def resolve_url(self, code: str, client_ip: str, 
                         count_click: bool = True) -> Tuple[int, str, str]:
        allowed, remaining = await self.repo.check_rate_limit(
            client_ip, self.rate_limit, self.rate_window
        )
        if not allowed:
            return 429, "", "Too Many Requests"
        
        status, url = await self.repo.resolve_url(code, count_click)
        
        if status == 200 and count_click:
            await self.repo.increment_click(code)
        
        error_msg = ""
        if status == 404:
            error_msg = "Link not found or expired"
        elif status == 410:
            error_msg = "Link expired (max clicks reached)"
        
        return status, url, error_msg
    
    async def get_top_links(self, limit: int = 10) -> List[dict]:
        limit = max(1, min(100, limit))
        links = await self.repo.get_top_links(limit)
        return [
            {"code": code, "clicks": clicks, "long_url": url}
            for code, clicks, url in links
        ]
    
    async def get_stats(self, code: str) -> Optional[dict]:
        stats = await self.repo.get_stats(code)
        if not stats:
            return None
        url = await self.repo.get_url(code)
        expired = (url is None)
        return {
            "code": code,
            "total_clicks": stats["total_clicks"],
            "created_at": stats["created_at"],
            "expired": expired
        }
    
    async def health_check(self) -> Tuple[str, bool]:
        redis_ok = await self.repo.ping()
        status = "ok" if redis_ok else "degraded"
        return status, redis_ok
