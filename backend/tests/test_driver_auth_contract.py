import pytest
from pydantic import ValidationError

from app.schemas.auth import DriverFirebaseLoginRequest, DriverFirebaseSignupRequest


def test_driver_login_request_accepts_only_a_firebase_token() -> None:
    request = DriverFirebaseLoginRequest(id_token="firebase-token")

    assert request.id_token == "firebase-token"


def test_driver_signup_requires_a_real_name() -> None:
    with pytest.raises(ValidationError):
        DriverFirebaseSignupRequest(id_token="firebase-token", full_name="")

    request = DriverFirebaseSignupRequest(id_token="firebase-token", full_name="Asha Driver")
    assert request.full_name == "Asha Driver"
