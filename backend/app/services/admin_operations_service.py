from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ride_hailing import Driver, DriverDocument, SupportTicket, Vehicle
from app.models.user import Passenger
from app.repositories.driver_repository import DriverRepository
from app.schemas.admin import (
    AdminDriverDocumentResponse,
    AdminDriverResponse,
    AdminSupportTicketResponse,
    AdminSupportTicketUpdate,
)


class AdminOperationsService:
    def __init__(self, driver_repository: DriverRepository | None = None) -> None:
        self.driver_repository = driver_repository or DriverRepository()

    def documents(self, db: Session, review_status: str | None) -> list[AdminDriverDocumentResponse]:
        query = select(DriverDocument, Driver).join(Driver, DriverDocument.driver_id == Driver.id).order_by(DriverDocument.created_at.asc())
        if review_status:
            query = query.where(DriverDocument.verification_status == review_status)
        items: list[AdminDriverDocumentResponse] = []
        for document, driver in db.execute(query).all():
            vehicle = self.driver_repository.get_active_vehicle(db, driver.id)
            items.append(AdminDriverDocumentResponse(
                driver_id=driver.id, driver_name=driver.full_name, operating_city=driver.operating_city,
                vehicle_registration_number=vehicle.registration_number if vehicle else None,
                document_type=document.document_type, document_number=document.document_number,
                verification_status=document.verification_status, review_note=document.review_note,
                created_at=document.created_at,
            ))
        return items

    def drivers(self, db: Session, driver_status: str | None) -> list[AdminDriverResponse]:
        query = select(Driver).order_by(Driver.created_at.desc())
        if driver_status:
            query = query.where(Driver.status == driver_status)
        results: list[AdminDriverResponse] = []
        for driver in db.scalars(query).all():
            vehicle = self.driver_repository.get_active_vehicle(db, driver.id)
            documents = self.driver_repository.get_documents(db, driver.id)
            results.append(AdminDriverResponse(
                id=driver.id, full_name=driver.full_name, phone_number=driver.phone_number,
                operating_city=driver.operating_city, status=driver.status,
                vehicle_category=vehicle.category_code if vehicle else None,
                vehicle_name=f'{vehicle.make} {vehicle.model}' if vehicle else None,
                vehicle_registration_number=vehicle.registration_number if vehicle else None,
                vehicle_verification_status=vehicle.verification_status if vehicle else None,
                document_statuses={document.document_type: document.verification_status for document in documents},
            ))
        return results

    def tickets(self, db: Session, ticket_status: str | None) -> list[AdminSupportTicketResponse]:
        query = select(SupportTicket, Passenger).join(Passenger, SupportTicket.passenger_id == Passenger.id).order_by(SupportTicket.created_at.desc())
        if ticket_status:
            query = query.where(SupportTicket.status == ticket_status)
        return [AdminSupportTicketResponse(
            id=ticket.id, passenger_name=passenger.full_name, category=ticket.category, status=ticket.status,
            subject=ticket.subject, description=ticket.description, created_at=ticket.created_at,
            assigned_admin_id=ticket.assigned_admin_id, resolution_note=ticket.resolution_note,
        ) for ticket, passenger in db.execute(query).all()]

    def update_ticket(self, db: Session, ticket_id: int, request: AdminSupportTicketUpdate, admin_id: int) -> AdminSupportTicketResponse:
        ticket = db.get(SupportTicket, ticket_id)
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Support ticket was not found.')
        ticket.status = request.status
        ticket.assigned_admin_id = admin_id
        ticket.resolution_note = request.resolution_note.strip() if request.resolution_note else None
        ticket.resolved_at = datetime.now(UTC) if request.status in {'resolved', 'closed'} else None
        db.add(ticket)
        db.commit()
        passenger = db.get(Passenger, ticket.passenger_id)
        return AdminSupportTicketResponse(id=ticket.id, passenger_name=passenger.full_name, category=ticket.category, status=ticket.status, subject=ticket.subject, description=ticket.description, created_at=ticket.created_at, assigned_admin_id=ticket.assigned_admin_id, resolution_note=ticket.resolution_note)
