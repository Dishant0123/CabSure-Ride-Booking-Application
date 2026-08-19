from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies.driver_auth import get_current_driver
from app.db import get_db
from app.models.ride_hailing import Driver
from app.schemas.auth import (
    DriverAuthResponse,
    DriverFirebaseLoginRequest,
    DriverOnboardingRequest,
    DriverProfileUpdateRequest,
    DriverProfileResponse,
    DriverRegistrationRequest,
    RefreshRequest,
)
from app.services.driver_auth_service import DriverAuthService

router = APIRouter(prefix="/auth/drivers", tags=["driver-auth"])
service = DriverAuthService()


@router.post("/firebase/login", response_model=DriverAuthResponse)
def firebase_login(
    request: DriverFirebaseLoginRequest, db: Session = Depends(get_db)
) -> DriverAuthResponse:
    return service.login(db, request)


@router.post("/firebase/register", response_model=DriverAuthResponse, status_code=status.HTTP_201_CREATED)
def register(request: DriverRegistrationRequest, db: Session = Depends(get_db)) -> DriverAuthResponse:
    return service.complete_registration(db, request)


@router.post("/refresh", response_model=DriverAuthResponse)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)) -> DriverAuthResponse:
    return service.refresh(db, request.refresh_token)


@router.get("/me", response_model=DriverProfileResponse)
def get_me(
    driver: Driver = Depends(get_current_driver), db: Session = Depends(get_db)
) -> DriverProfileResponse:
    return service.profile(db, driver)


@router.patch('/me', response_model=DriverProfileResponse)
def update_me(
    request: DriverProfileUpdateRequest,
    driver: Driver = Depends(get_current_driver), db: Session = Depends(get_db)
) -> DriverProfileResponse:
    return service.update_profile(db, driver, request)


@router.post("/onboarding", response_model=DriverProfileResponse)
def complete_onboarding(
    request: DriverOnboardingRequest,
    driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
) -> DriverProfileResponse:
    return service.complete_onboarding(db, driver, request)
