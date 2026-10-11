from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# SQLite for simplicity — swap to PostgreSQL in production
# just change this URL to: postgresql://user:pass@localhost/dbname
DATABASE_URL = "sqlite:///./urls.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # needed for SQLite only
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Model ──────────────────────────────────────────────────
class URL(Base):
    __tablename__ = "urls"

    id         = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, index=True)   # e.g. "abc123"
    original   = Column(String, nullable=False)             # e.g. "https://google.com"
    clicks     = Column(Integer, default=0)                 # hit counter
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Helpers ────────────────────────────────────────────────
def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session, always closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
