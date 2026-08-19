from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class AdminLoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=8, max_length=128)

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class AdminProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    permissions: list[str]
    last_login_at: datetime | None = None


class AdminAuthResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    admin: AdminProfileResponse


class AdminPasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)

    @model_validator(mode='after')
    def passwords_must_differ(self) -> 'AdminPasswordChangeRequest':
        if self.current_password == self.new_password:
            raise ValueError('Choose a new password different from the current password.')
        return self


class AdminPasswordChangeResponse(BaseModel):
    message: str


class AdminDriverDocumentResponse(BaseModel):
    driver_id: int
    driver_name: str
    operating_city: str | None
    vehicle_registration_number: str | None
    document_type: str
    document_number: str
    verification_status: str
    review_note: str | None
    created_at: datetime


class AdminDriverResponse(BaseModel):
    id: int
    full_name: str
    phone_number: str
    operating_city: str | None
    status: str
    vehicle_category: str | None
    vehicle_name: str | None
    vehicle_registration_number: str | None
    vehicle_verification_status: str | None
    document_statuses: dict[str, str]


TicketStatus = Literal['open', 'in_progress', 'resolved', 'closed']


class AdminSupportTicketResponse(BaseModel):
    id: int
    passenger_name: str
    category: str
    status: str
    subject: str
    description: str
    created_at: datetime
    assigned_admin_id: int | None
    resolution_note: str | None


class AdminSupportTicketUpdate(BaseModel):
    status: TicketStatus
    resolution_note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode='after')
    def resolution_needs_a_note(self) -> 'AdminSupportTicketUpdate':
        if self.status in {'resolved', 'closed'} and not (self.resolution_note or '').strip():
            raise ValueError('Add a resolution note before resolving or closing a ticket.')
        return self
