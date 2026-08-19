from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.admin_auth import get_current_admin, require_admin_permission
from app.db import get_db
from app.models.user import AdminUser
from app.schemas.admin import (
    AdminAuthResponse, AdminDriverDocumentResponse, AdminDriverResponse, AdminLoginRequest,
    AdminPasswordChangeRequest, AdminPasswordChangeResponse, AdminProfileResponse,
    AdminSupportTicketResponse, AdminSupportTicketUpdate,
)
from app.schemas.admin_review import DriverDocumentReviewRequest, DriverDocumentReviewResponse
from app.services.admin_auth_service import AdminAuthService
from app.services.admin_operations_service import AdminOperationsService
from app.services.driver_document_review_service import DriverDocumentReviewService

router = APIRouter(prefix='/admin', tags=['admin'])
auth_service = AdminAuthService()
operations_service = AdminOperationsService()
document_service = DriverDocumentReviewService()


@router.post('/auth/login', response_model=AdminAuthResponse)
def login(request: AdminLoginRequest, db: Session = Depends(get_db)) -> AdminAuthResponse:
    return auth_service.login(db, request)


@router.get('/auth/me', response_model=AdminProfileResponse)
def me(admin: AdminUser = Depends(get_current_admin)) -> AdminProfileResponse:
    return auth_service._profile(admin)


@router.post('/auth/change-password', response_model=AdminPasswordChangeResponse)
def change_password(request: AdminPasswordChangeRequest, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)) -> AdminPasswordChangeResponse:
    auth_service.change_password(db, admin, request)
    return AdminPasswordChangeResponse(message='Password changed. Sign in again with your new password.')


@router.get('/drivers', response_model=list[AdminDriverResponse])
def list_drivers(driver_status: str | None = None, _: AdminUser = Depends(require_admin_permission('drivers:read')), db: Session = Depends(get_db)) -> list[AdminDriverResponse]:
    return operations_service.drivers(db, driver_status)


@router.get('/driver-documents', response_model=list[AdminDriverDocumentResponse])
def list_driver_documents(status_filter: str | None = None, _: AdminUser = Depends(require_admin_permission('drivers:read')), db: Session = Depends(get_db)) -> list[AdminDriverDocumentResponse]:
    return operations_service.documents(db, status_filter)


@router.put('/drivers/{driver_id}/documents/{document_type}/review', response_model=DriverDocumentReviewResponse)
def review_driver_document(driver_id: int, document_type: str, request: DriverDocumentReviewRequest, admin: AdminUser = Depends(require_admin_permission('documents:review')), db: Session = Depends(get_db)) -> DriverDocumentReviewResponse:
    return document_service.review(db, driver_id, document_type, request, admin.email)


@router.get('/support-tickets', response_model=list[AdminSupportTicketResponse])
def list_support_tickets(ticket_status: str | None = None, _: AdminUser = Depends(require_admin_permission('support:manage')), db: Session = Depends(get_db)) -> list[AdminSupportTicketResponse]:
    return operations_service.tickets(db, ticket_status)


@router.patch('/support-tickets/{ticket_id}', response_model=AdminSupportTicketResponse)
def update_support_ticket(ticket_id: int, request: AdminSupportTicketUpdate, admin: AdminUser = Depends(require_admin_permission('support:manage')), db: Session = Depends(get_db)) -> AdminSupportTicketResponse:
    return operations_service.update_ticket(db, ticket_id, request, admin.id)
