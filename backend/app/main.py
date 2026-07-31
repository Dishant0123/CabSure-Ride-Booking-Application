from fastapi import FastAPI

from app.api.v1.router import api_router
from app.api.v1.routes.health import router as health_router
from app.core.config import get_settings
from app.db import initialize_database
import app.models  # noqa: F401


def create_app() -> FastAPI:
    settings = get_settings()
    initialize_database()
    app = FastAPI(title=settings.app_name)
    app.include_router(health_router, tags=['health'])
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
