from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .database import get_db
from .schemas import ShortenRequest, ShortenResponse, StatsResponse
from . import service

router = APIRouter()

BASE_URL = "http://localhost:8000"


# ── POST /shorten ──────────────────────────────────────────
# Client sends: { "url": "https://google.com" }
# Server returns: { "short_code": "abc123", "short_url": "http://localhost:8000/abc123", ... }
@router.post("/shorten", response_model=ShortenResponse)
def shorten_url(body: ShortenRequest, db: Session = Depends(get_db)):
    """
    Shorten a long URL.
    Optionally pass custom_code for a custom short URL.
    """
    url_obj = service.create_short_url(
        db=db,
        original=str(body.url),
        custom_code=body.custom_code
    )
    return ShortenResponse(
        short_code=url_obj.short_code,
        short_url=f"{BASE_URL}/{url_obj.short_code}",
        original=url_obj.original,
        created_at=url_obj.created_at
    )


# ── GET /{code} ────────────────────────────────────────────
# Client visits: http://localhost:8000/abc123
# Server redirects to: https://google.com
@router.get("/{short_code}")
def redirect_url(short_code: str, db: Session = Depends(get_db)):
    """
    Resolve a short code and redirect to original URL.
    Increments click counter on every hit.
    301 = permanent redirect (browser caches it)
    302 = temporary redirect (browser always asks server)
    Using 302 here so click counter always gets hit.
    """
    url_obj = service.get_original_url(db=db, short_code=short_code)
    return RedirectResponse(url=url_obj.original, status_code=302)


# ── GET /stats/{code} ─────────────────────────────────────
# Returns analytics for a short URL
@router.get("/stats/{short_code}", response_model=StatsResponse)
def get_stats(short_code: str, db: Session = Depends(get_db)):
    """
    Get stats for a short URL — clicks, original URL, created date.
    Does NOT increment click counter.
    """
    url_obj = service.get_stats(db=db, short_code=short_code)
    return StatsResponse(
        short_code=url_obj.short_code,
        original=url_obj.original,
        clicks=url_obj.clicks,
        created_at=url_obj.created_at
    )


# ── DELETE /{code} ─────────────────────────────────────────
@router.delete("/{short_code}")
def delete_url(short_code: str, db: Session = Depends(get_db)):
    """Delete a short URL."""
    return service.delete_short_url(db=db, short_code=short_code)
