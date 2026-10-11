from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional          # ← add this import

from .database import URL
from .utils import generate_short_code


# ── Shorten ────────────────────────────────────────────────
def create_short_url(db: Session, original: str, custom_code: Optional[str]) -> URL:
    """
    1. If custom_code provided → use it (check not taken)
    2. Otherwise → generate random code
    3. Check for duplicate original URL (optional dedup)
    4. Save to DB
    """

    # check if this original URL already shortened
    existing = db.query(URL).filter(URL.original == original).first()
    if existing:
        return existing  # return existing instead of creating duplicate

    # determine short code
    if custom_code:
        # check custom code not already taken
        taken = db.query(URL).filter(URL.short_code == custom_code).first()
        if taken:
            raise HTTPException(
                status_code=400,
                detail=f"Custom code '{custom_code}' is already taken"
            )
        code = custom_code
    else:
        # generate unique random code
        # keep retrying if collision (extremely rare but handle it)
        for _ in range(5):
            code = generate_short_code()
            if not db.query(URL).filter(URL.short_code == code).first():
                break
        else:
            raise HTTPException(
                status_code=500,
                detail="Could not generate unique code, try again"
            )

    # save to DB
    url_obj = URL(short_code=code, original=original)
    db.add(url_obj)
    db.commit()
    db.refresh(url_obj)
    return url_obj


# ── Resolve ────────────────────────────────────────────────
def get_original_url(db: Session, short_code: str) -> URL:
    """Look up short code → return original URL, increment click counter."""
    url_obj = db.query(URL).filter(URL.short_code == short_code).first()
    if not url_obj:
        raise HTTPException(status_code=404, detail="Short URL not found")

    # increment click counter
    url_obj.clicks += 1
    db.commit()
    return url_obj


# ── Stats ──────────────────────────────────────────────────
def get_stats(db: Session, short_code: str) -> URL:
    """Return stats for a short code without incrementing clicks."""
    url_obj = db.query(URL).filter(URL.short_code == short_code).first()
    if not url_obj:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return url_obj


# ── Delete ─────────────────────────────────────────────────
def delete_short_url(db: Session, short_code: str) -> dict:
    """Delete a short URL by its code."""
    url_obj = db.query(URL).filter(URL.short_code == short_code).first()
    if not url_obj:
        raise HTTPException(status_code=404, detail="Short URL not found")
    db.delete(url_obj)
    db.commit()
    return {"message": f"'{short_code}' deleted successfully"}
