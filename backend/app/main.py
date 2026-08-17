from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routes import meetings, sessions
from app.routes import settings as settings_routes

app_settings = get_settings()

app = FastAPI(title="Ticket Generator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(settings_routes.router, prefix="/api")
app.include_router(meetings.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok"}
