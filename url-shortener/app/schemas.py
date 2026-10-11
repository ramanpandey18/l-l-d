from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class ShortenRequest(BaseModel):
    url: HttpUrl
    custom_code: Optional[str] = None


class ShortenResponse(BaseModel):
    short_code: str
    short_url:  str
    original:   str
    created_at: datetime


class StatsResponse(BaseModel):
    short_code: str
    original:   str
    clicks:     int
    created_at: datetime