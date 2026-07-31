import secrets
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import Passenger
from app.repositories.passenger_repository import PassengerRepository
from app.schemas.auth import PassengerSignupRequest, TokenResponse
from app.services.firebase_service import initialize_firebase

password_hash = PasswordHash.recommended()


class AuthService:
    def __init__(self, repository: PassengerRepository | None = None):
        self.repository = repository or PassengerRepository()
        self.settings = get_settings()

    def signup(self, db: Session, request: PassengerSignupRequest) -> Passenger:
        if self.repository.get_by_phone(db, request.phone_number):
            raise HTTPException(status_code=409, detail='An account already exists for this phone number.')
        return self.repository.create(db, Passenger(full_name=request.full_name, phone_number=request.phone_number, password_hash=password_hash.hash(request.password)))

    def request_otp(self, db: Session, phone_number: str) -> str:
        passenger = self.repository.get_by_phone(db, phone_number)
        if not passenger:
            # OTP login is passwordless on the Passenger app. A minimal pending
            # account is created here and becomes authenticated only after OTP verification.
            passenger = self.repository.create(
                db,
                Passenger(
                    full_name='Passenger',
                    phone_number=phone_number,
                    password_hash=password_hash.hash(secrets.token_urlsafe(32)),
                ),
            )
        otp = f'{secrets.randbelow(1_000_000):06d}'
        passenger.otp_hash = password_hash.hash(otp)
        passenger.otp_expires_at = datetime.now(UTC) + timedelta(minutes=self.settings.otp_expiry_minutes)
        self.repository.save(db, passenger)
        return otp

    def verify_otp(self, db: Session, phone_number: str, otp: str) -> TokenResponse:
        passenger = self._get_passenger(db, phone_number)
        if not passenger.otp_hash or not passenger.otp_expires_at or passenger.otp_expires_at < datetime.now(UTC) or not password_hash.verify(otp, passenger.otp_hash):
            raise HTTPException(status_code=400, detail='Invalid or expired OTP.')
        passenger.is_phone_verified = True
        passenger.otp_hash = None
        passenger.otp_expires_at = None
        self.repository.save(db, passenger)
        return self._tokens(passenger)

    def login(self, db: Session, phone_number: str, password: str) -> TokenResponse:
        passenger = self._get_passenger(db, phone_number)
        if not password_hash.verify(password, passenger.password_hash):
            raise HTTPException(status_code=401, detail='Invalid phone number or password.')
        if not passenger.is_phone_verified:
            raise HTTPException(status_code=403, detail='Verify your phone number before logging in.')
        return self._tokens(passenger)

    def refresh(self, refresh_token: str) -> TokenResponse:
        payload = self._decode(refresh_token, 'refresh')
        passenger = Passenger(id=int(payload['sub']), full_name='', phone_number='', password_hash='')
        return self._tokens(passenger)

    def firebase_login(self, db: Session, id_token: str, full_name: str | None = None) -> TokenResponse:
        firebase_uid, phone_number = self._verified_firebase_identity(id_token)
        passenger = self.repository.get_by_firebase_uid(db, firebase_uid) or self.repository.get_verified_by_phone(db, phone_number)
        if not passenger:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No verified Cab Sure account exists for this number. Please sign up first.')
        passenger.firebase_uid = firebase_uid
        passenger.is_phone_verified = True
        passenger.last_login_at = datetime.now(UTC)
        self.repository.save(db, passenger)
        return self._tokens(passenger)

    def firebase_signup(self, db: Session, id_token: str, full_name: str | None) -> TokenResponse:
        firebase_uid, phone_number = self._verified_firebase_identity(id_token)
        existing = self.repository.get_by_firebase_uid(db, firebase_uid) or self.repository.get_by_phone(db, phone_number)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='An account already exists for this number. Please log in.')
        passenger = Passenger(
            full_name=full_name.strip() if full_name else 'Passenger',
            phone_number=phone_number,
            firebase_uid=firebase_uid,
            password_hash=password_hash.hash(secrets.token_urlsafe(32)),
            is_phone_verified=True,
            last_login_at=datetime.now(UTC),
        )
        passenger = self.repository.create(db, passenger)
        self.repository.create_profile(db, passenger.id)
        return self._tokens(passenger)

    def ensure_firebase_login_allowed(self, db: Session, phone_number: str) -> None:
        if not self.repository.get_verified_by_phone(db, phone_number):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No verified Cab Sure account exists for this number. Please sign up first.')

    def _verified_firebase_identity(self, id_token: str) -> tuple[str, str]:
        initialize_firebase()
        try:
            decoded = firebase_auth.verify_id_token(id_token)
        except Exception as error:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Firebase could not verify this phone session.') from error

        firebase_uid = decoded.get('uid')
        phone_number = decoded.get('phone_number')
        if not firebase_uid or not phone_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='A verified Firebase phone number is required.')
        return firebase_uid, ''.join(character for character in phone_number if character.isdigit())

    def _tokens(self, passenger: Passenger) -> TokenResponse:
        return TokenResponse(access_token=self._encode(passenger.id, 'access', timedelta(minutes=self.settings.access_token_minutes)), refresh_token=self._encode(passenger.id, 'refresh', timedelta(days=self.settings.refresh_token_days)))

    def _encode(self, passenger_id: int, token_type: str, expires_in: timedelta) -> str:
        return jwt.encode({'sub': str(passenger_id), 'type': token_type, 'exp': datetime.now(UTC) + expires_in}, self.settings.jwt_secret_key, algorithm=self.settings.jwt_algorithm)

    def _decode(self, token: str, token_type: str) -> dict:
        try:
            payload = jwt.decode(token, self.settings.jwt_secret_key, algorithms=[self.settings.jwt_algorithm])
            if payload.get('type') != token_type:
                raise ValueError
            return payload
        except (jwt.PyJWTError, ValueError) as error:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token.') from error

    def _get_passenger(self, db: Session, phone_number: str) -> Passenger:
        passenger = self.repository.get_by_phone(db, phone_number)
        if not passenger:
            raise HTTPException(status_code=404, detail='No account exists for this phone number.')
        return passenger
