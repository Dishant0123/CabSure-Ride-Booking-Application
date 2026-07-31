from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_passenger
from app.db import get_db
from app.models.user import Passenger
from app.schemas.booking import LocationOptionResponse, RideBookingResponse, RideEstimateRequest, RideEstimateResponse, UpdateSavedPlaceRequest
from app.schemas.home import PlaceResponse
from app.services.booking_service import BookingService

router = APIRouter(prefix='/passengers/me', tags=['passenger-booking'])
service = BookingService()


@router.get('/locations', response_model=list[LocationOptionResponse])
def get_locations(_: Passenger = Depends(get_current_passenger), db: Session = Depends(get_db)) -> list[LocationOptionResponse]:
    return service.locations(db)


@router.post('/ride-estimates', response_model=RideEstimateResponse)
def estimate_ride(request: RideEstimateRequest, _: Passenger = Depends(get_current_passenger), db: Session = Depends(get_db)) -> RideEstimateResponse:
    return service.estimate(db, request)


@router.post('/rides', response_model=RideBookingResponse, status_code=status.HTTP_201_CREATED)
def book_ride(request: RideEstimateRequest, passenger: Passenger = Depends(get_current_passenger), db: Session = Depends(get_db)) -> RideBookingResponse:
    return service.book(db, passenger, request)


@router.patch('/saved-places/{saved_place_id}', response_model=PlaceResponse)
def update_saved_place(saved_place_id: int, request: UpdateSavedPlaceRequest, passenger: Passenger = Depends(get_current_passenger), db: Session = Depends(get_db)) -> PlaceResponse:
    return service.update_saved_place(db, passenger, saved_place_id, request.location_id)
