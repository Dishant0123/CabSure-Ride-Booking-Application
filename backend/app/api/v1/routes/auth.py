from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.schemas.auth import FirebaseLoginRequest, OtpRequest, OtpRequestResponse, OtpVerificationRequest, PassengerSignupRequest, PasswordLoginRequest, RefreshRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix='/auth/passengers', tags=['passenger-auth'])
service = AuthService()


@router.post('/signup', response_model=OtpRequestResponse, status_code=status.HTTP_201_CREATED)
def signup(request: PassengerSignupRequest, db: Session = Depends(get_db)) -> OtpRequestResponse:
    passenger = service.signup(db, request)
    otp = service.request_otp(db, passenger.phone_number)
    return OtpRequestResponse(message='Account created. Verify the OTP to continue.', development_otp=otp if get_settings().environment == 'development' else None)


@router.post('/otp/request', response_model=OtpRequestResponse)
def request_otp(request: OtpRequest, db: Session = Depends(get_db)) -> OtpRequestResponse:
    otp = service.request_otp(db, request.phone_number)
    return OtpRequestResponse(message='OTP sent.', development_otp=otp if get_settings().environment == 'development' else None)


@router.post('/otp/verify', response_model=TokenResponse)
def verify_otp(request: OtpVerificationRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return service.verify_otp(db, request.phone_number, request.otp)


@router.post('/login', response_model=TokenResponse)
def login(request: PasswordLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return service.login(db, request.phone_number, request.password)


@router.post('/refresh', response_model=TokenResponse)
def refresh(request: RefreshRequest) -> TokenResponse:
    return service.refresh(request.refresh_token)


@router.post('/firebase/login', response_model=TokenResponse)
def firebase_login(request: FirebaseLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return service.firebase_login(db, request.id_token)


@router.post('/firebase/signup', response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def firebase_signup(request: FirebaseLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return service.firebase_signup(db, request.id_token, request.full_name)


@router.post('/firebase/login/preflight', status_code=status.HTTP_204_NO_CONTENT)
def firebase_login_preflight(request: OtpRequest, db: Session = Depends(get_db)) -> None:
    service.ensure_firebase_login_allowed(db, request.phone_number)
