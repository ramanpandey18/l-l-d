from fastapi import FastAPI
from .database import create_tables
from .routes import router

app = FastAPI(
    title="URL Shortener",
    description="A simple URL shortener API built with FastAPI + SQLite",
    version="1.0.0"
)

# create DB tables on startup
@app.on_event("startup")
def startup():
    create_tables()

# register all routes
app.include_router(router)
