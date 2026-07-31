from pydantic import BaseModel, Field, field_validator


def normalize_phone(value: str) -> str:
    digits = ''.join(character for character in value if character.isdigit())
    if len(digits) == 10 and digits[0] in '6789':
        return f'91{digits}'
    if len(digits) == 12 and digits.startswith('91') and digits[2] in '6789':
        return digits
    raise ValueError('Enter a valid 10-digit Indian mobile number.')


class PassengerSignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone_number: str = Field(min_length=10, max_length=20)
    password: str = Field(min_length=8, max_length=128)

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = normalize_phone(value)
        return normalized


class PasswordLoginRequest(BaseModel):
    phone_number: str
    password: str = Field(min_length=8, max_length=128)

    _normalize_phone = field_validator('phone_number')(normalize_phone)


class OtpRequest(BaseModel):
    phone_number: str
    _normalize_phone = field_validator('phone_number')(normalize_phone)


class OtpVerificationRequest(OtpRequest):
    otp: str = Field(pattern=r'^\d{6}$')


class RefreshRequest(BaseModel):
    refresh_token: str


class FirebaseLoginRequest(BaseModel):
    id_token: str = Field(min_length=1)
    full_name: str | None = Field(default=None, min_length=2, max_length=120)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class OtpRequestResponse(BaseModel):
    message: str
    development_otp: str | None = None
