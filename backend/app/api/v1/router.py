from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.booking import router as booking_router
from app.api.v1.routes.emergency_contacts import router as emergency_contacts_router
from app.api.v1.routes.home import router as home_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(home_router)
api_router.include_router(booking_router)
api_router.include_router(emergency_contacts_router)
