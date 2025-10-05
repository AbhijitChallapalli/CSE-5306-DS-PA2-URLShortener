# File: common/lib/models.py
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class ShortenRequest(BaseModel):
    long_url: HttpUrl
    ttl_sec: Optional[int] = Field(default=None, ge=1)
    max_clicks: Optional[int] = Field(default=None, ge=1)

class ShortenResponse(BaseModel):
    code: str
    short_url: str

class ResolveResponse(BaseModel):
    long_url: str
