from datetime import UTC, datetime
from math import asin, cos, radians, sin, sqrt

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ride_hailing import FareLineItem, FareQuote, LocationCatalog, Ride, RideCategory, RideEvent, SavedPlace
from app.models.user import Passenger
from app.schemas.booking import FareItemResponse, LocationOptionResponse, RideBookingResponse, RideEstimateRequest, RideEstimateResponse
from app.schemas.home import PlaceResponse


class BookingService:
    catalog = (
        ('IIT Dharwad', 'IIT Dharwad, Karnataka', 15.4565, 74.9690),
        ('Hubballi Railway Station', 'Railway Station Road, Hubballi, Karnataka', 15.3518, 75.1379),
        ('Vidyanagar', 'Vidyanagar, Hubballi, Karnataka', 15.3647, 75.1239),
        ('KLE Technological University', 'BVB Campus, Hubballi, Karnataka', 15.3643, 75.1195),
        ('Urban Oasis Mall', 'Gokul Road, Hubballi, Karnataka', 15.3530, 75.1370),
    )

    def locations(self, db: Session) -> list[LocationOptionResponse]:
        if not db.scalar(select(LocationCatalog.id).limit(1)):
            db.add_all(LocationCatalog(name=name, formatted_address=address, latitude=latitude, longitude=longitude) for name, address, latitude, longitude in self.catalog)
            db.commit()
        return [self._location(item) for item in db.scalars(select(LocationCatalog).order_by(LocationCatalog.name)).all()]

    def estimate(self, db: Session, request: RideEstimateRequest) -> RideEstimateResponse:
        pickup, destination = self._locations_for_request(db, request)
        category = db.get(RideCategory, request.category_id)
        if not category or not category.is_active:
            raise HTTPException(status_code=404, detail='Ride category is not available.')
        distance_km = round(max(1.2, self._distance(pickup, destination)), 1)
        duration = max(4, round(distance_km * 3.2))
        distance_charge = int(distance_km * 1200)
        fare = category.base_fare_paise + distance_charge
        return RideEstimateResponse(pickup=self._location(pickup), destination=self._location(destination), category_name=category.display_name, distance_km=distance_km, duration_minutes=duration, fare_paise=fare, fare_items=[FareItemResponse(label='Base fare', amount_paise=category.base_fare_paise), FareItemResponse(label='Distance charge', amount_paise=distance_charge)])

    def book(self, db: Session, passenger: Passenger, request: RideEstimateRequest) -> RideBookingResponse:
        estimate = self.estimate(db, request)
        category = db.get(RideCategory, request.category_id)
        ride = Ride(passenger_id=passenger.id, category_id=category.id, status='searching', pickup_address=estimate.pickup.formatted_address, pickup_latitude=estimate.pickup.latitude, pickup_longitude=estimate.pickup.longitude, destination_address=estimate.destination.formatted_address, destination_latitude=estimate.destination.latitude, destination_longitude=estimate.destination.longitude, requested_at=datetime.now(UTC), estimated_distance_meters=round(estimate.distance_km * 1000), estimated_duration_seconds=estimate.duration_minutes * 60)
        db.add(ride); db.flush()
        quote = FareQuote(ride_id=ride.id, amount_paise=estimate.fare_paise, is_final=False); db.add(quote); db.flush()
        db.add_all(FareLineItem(fare_quote_id=quote.id, item_type=item.label.lower().replace(' ', '_'), amount_paise=item.amount_paise) for item in estimate.fare_items)
        db.add(RideEvent(ride_id=ride.id, actor_type='passenger', actor_id=passenger.id, event_type='ride_requested', payload={'fare_paise': estimate.fare_paise}))
        db.commit(); db.refresh(ride)
        return RideBookingResponse(ride_id=ride.id, status=ride.status, pickup_address=ride.pickup_address, destination_address=ride.destination_address, fare_paise=estimate.fare_paise, requested_at=ride.requested_at)

    def update_saved_place(self, db: Session, passenger: Passenger, saved_place_id: int, location_id: int) -> PlaceResponse:
        saved_place = db.scalar(select(SavedPlace).where(SavedPlace.id == saved_place_id, SavedPlace.passenger_id == passenger.id))
        if not saved_place:
            raise HTTPException(status_code=404, detail='Saved place was not found.')
        location = db.get(LocationCatalog, location_id)
        if not location:
            raise HTTPException(status_code=404, detail='Selected location is unavailable.')
        saved_place.formatted_address = location.formatted_address
        saved_place.latitude = location.latitude
        saved_place.longitude = location.longitude
        db.commit()
        db.refresh(saved_place)
        return PlaceResponse(
            id=saved_place.id,
            label=saved_place.label,
            formatted_address=saved_place.formatted_address,
            latitude=float(saved_place.latitude),
            longitude=float(saved_place.longitude),
        )

    def _locations_for_request(self, db: Session, request: RideEstimateRequest) -> tuple[LocationCatalog, LocationCatalog]:
        if request.pickup_location_id == request.destination_location_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Pickup and destination must be different.')
        pickup, destination = db.get(LocationCatalog, request.pickup_location_id), db.get(LocationCatalog, request.destination_location_id)
        if not pickup or not destination:
            raise HTTPException(status_code=404, detail='Selected location is unavailable.')
        return pickup, destination

    @staticmethod
    def _location(item: LocationCatalog) -> LocationOptionResponse:
        return LocationOptionResponse(id=item.id, name=item.name, formatted_address=item.formatted_address, latitude=float(item.latitude), longitude=float(item.longitude))

    @staticmethod
    def _distance(a: LocationCatalog, b: LocationCatalog) -> float:
        lat1, lon1, lat2, lon2 = map(radians, (float(a.latitude), float(a.longitude), float(b.latitude), float(b.longitude)))
        value = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
        return 6371 * 2 * asin(sqrt(value))
