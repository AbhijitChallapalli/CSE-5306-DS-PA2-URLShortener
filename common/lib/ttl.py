# File: common/lib/ttl.py
from typing import Optional

def normalize_ttl(ttl_sec: Optional[int]) -> Optional[int]:
    if ttl_sec is None:
        return None
    return max(1, int(ttl_sec))
