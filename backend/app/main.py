import logging
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registra as tabelas)
from app.core.config import settings
from app.database import SessionLocal
from app.routers import (analytics, auth, automation, dashboard, links, progress, reports, schedules, sessions,
                         users, workouts)
from app.seed import ensure_base_data, seed

API = "/api/v1"
log = logging.getLogger("trainup")


def run_migrations() -> None:
    cfg = Config()
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parent.parent / "alembic"))
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_migrations()
    with SessionLocal() as db:
        if settings.SEED_DEMO:
            seed(db)
        else:
            ensure_base_data(db)
    yield


app = FastAPI(
    title="TrainUp API", version="0.3.0", lifespan=lifespan,
    docs_url="/api/docs" if settings.ENABLE_DOCS else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if settings.ENABLE_DOCS else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, users, links, workouts, schedules, progress, sessions, analytics, reports, automation, dashboard):
    app.include_router(r.router, prefix=API)


@app.get("/api/health", tags=["Infra"])
def health():
    return {"status": "ok"}
