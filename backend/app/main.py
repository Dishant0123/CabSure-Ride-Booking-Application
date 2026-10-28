from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import app.models  # noqa: F401
from app.api.v1.router import api_router
from app.api.v1.routes.health import router as health_router
from app.core.config import get_settings
from app.db import SessionLocal, initialize_database
from app.services.admin_auth_service import AdminAuthService
from app.services.realtime_service import realtime_hub


@asynccontextmanager
async def lifespan(_: FastAPI):
    realtime_hub.bind_running_loop()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    initialize_database()
    db = SessionLocal()
    try:
        AdminAuthService().bootstrap(db)
    finally:
        db.close()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.include_router(health_router, tags=["health"])
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    admin_app_directory = Path(__file__).resolve().parents[2] / "admin-app"
    if admin_app_directory.is_dir():
        app.mount("/admin", StaticFiles(directory=admin_app_directory, html=True), name="admin-app")
    return app


app = create_app()
