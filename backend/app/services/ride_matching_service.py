from datetime import UTC, datetime, timedelta
from math import asin, cos, radians, sin, sqrt

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ride_hailing import (
    Driver, DriverCurrentLocation, DriverVehicleAssignment, FareQuote, Ride,
    RideDispatchOffer, RideEvent, RideCategory, Vehicle,
)
from app.schemas.booking import (
    DriverRideOfferDecisionResponse, DriverRideOfferResponse, PassengerRideStatusResponse,
)
from app.services.realtime_events import (
    publish_driver_location,
    publish_driver_offer,
    publish_driver_offer_cleared,
    publish_passenger_status,
)
from app.services.ride_lifecycle_service import RideLifecycleService
from app.services.driver_readiness_service import DriverReadinessService


class RideMatchingService:
    """Durable local dispatch implementation; replace candidate lookup with Redis/PostGIS in production."""

    offer_ttl = timedelta(seconds=30)
    # Dharwad and Hubballi operate as one demo dispatch region. This remains a
    # distance constraint, but covers trips across the twin-city area.
    maximum_pickup_distance_km = 40.0
    city_centres = {
        'dharwad': (15.4589, 75.0078),
        'hubballi': (15.3647, 75.1240),
        'hubli': (15.3647, 75.1240),
    }
    readiness_service = DriverReadinessService()

    def dispatch(self, db: Session, ride: Ride) -> RideDispatchOffer | None:
        if ride.status != 'searching':
            return None
        offered_driver_ids = set(db.scalars(select(RideDispatchOffer.driver_id).where(RideDispatchOffer.ride_id == ride.id)))
        candidate = self._nearest_candidate(db, ride, offered_driver_ids)
        if not candidate:
            ride.status = 'cancelled'
            ride.cancelled_at = datetime.now(UTC)
            ride.cancellation_reason = 'no_eligible_driver'
            db.add(RideEvent(ride_id=ride.id, actor_type='system', actor_id=None, event_type='matching_failed', payload={'reason': ride.cancellation_reason}))
            return None
        offer = RideDispatchOffer(ride_id=ride.id, driver_id=candidate[0].id, expires_at=datetime.now(UTC) + self.offer_ttl)
        db.add(offer)
        db.add(RideEvent(ride_id=ride.id, actor_type='system', actor_id=None, event_type='ride_offered', payload={'driver_id': candidate[0].id, 'pickup_distance_km': candidate[1]}))
        return offer

    def current_offer(self, db: Session, driver: Driver) -> DriverRideOfferResponse | None:
        now = datetime.now(UTC)
        offer = db.scalar(select(RideDispatchOffer).where(
            RideDispatchOffer.driver_id == driver.id,
            RideDispatchOffer.status == 'pending',
        ).order_by(RideDispatchOffer.offered_at.desc()))
        if not offer:
            return None
        if self._is_expired(offer, now):
            next_offer = self._expire_and_retry(db, offer)
            db.commit()
            publish_driver_offer_cleared(driver.id, offer.ride_id)
            ride = db.get(Ride, offer.ride_id)
            if ride:
                publish_passenger_status(db, ride)
            if next_offer:
                publish_driver_offer(db, next_offer)
            return None
        ride = db.get(Ride, offer.ride_id)
        if not ride or ride.status != 'searching':
            return None
        quote = db.scalar(select(FareQuote).where(FareQuote.ride_id == ride.id).order_by(FareQuote.created_at.desc()))
        return DriverRideOfferResponse(
            offer_id=offer.id, ride_id=ride.id, pickup_address=ride.pickup_address,
            destination_address=ride.destination_address,
            estimated_distance_km=round((ride.estimated_distance_meters or 0) / 1000, 1),
            expected_fare_paise=quote.amount_paise if quote else 0,
            pickup_minutes_away=4, expires_at=offer.expires_at,
            pickup_latitude=float(ride.pickup_latitude), pickup_longitude=float(ride.pickup_longitude),
            destination_latitude=float(ride.destination_latitude), destination_longitude=float(ride.destination_longitude),
        )

    def respond(self, db: Session, driver: Driver, offer_id: int, decision: str) -> DriverRideOfferDecisionResponse:
        offer = db.scalar(select(RideDispatchOffer).where(RideDispatchOffer.id == offer_id, RideDispatchOffer.driver_id == driver.id))
        if not offer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Ride offer was not found.')
        if offer.status != 'pending' or self._is_expired(offer, datetime.now(UTC)):
            if offer.status == 'pending':
                self._expire_and_retry(db, offer)
                db.commit()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='This ride offer has expired. We are finding the next Driver.')
        ride = db.get(Ride, offer.ride_id)
        if not ride or ride.status != 'searching':
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='This ride is no longer available.')

        offer.status, offer.responded_at = decision, datetime.now(UTC)
        next_offer = None
        if decision == 'accepted':
            existing = db.scalar(select(Ride).where(
                Ride.driver_id == driver.id,
                Ride.status.in_(('driver_assigned', 'driver_arriving', 'driver_arrived', 'in_progress')),
                Ride.id != ride.id,
            ))
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Finish active ride #{existing.id} before accepting another request.')
            vehicle = self._active_vehicle(db, driver.id)
            if not vehicle or vehicle.verification_status != 'verified' or not driver.is_online:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Go online with a verified vehicle before accepting rides.')
            ride.driver_id, ride.vehicle_id = driver.id, vehicle.id
            ride.status, ride.accepted_at = 'driver_arriving', datetime.now(UTC)
            db.add(RideEvent(ride_id=ride.id, actor_type='driver', actor_id=driver.id, event_type='ride_accepted', payload={'offer_id': offer.id}))
            message = 'Ride accepted. The passenger has been notified that you are on the way.'
        else:
            db.add(RideEvent(ride_id=ride.id, actor_type='driver', actor_id=driver.id, event_type='ride_declined', payload={'offer_id': offer.id}))
            next_offer = self.dispatch(db, ride)
            message = 'Ride declined. We are offering it to another eligible Driver.'
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='You already have another active ride.') from exc
        db.refresh(ride)
        publish_driver_offer_cleared(driver.id, ride.id)
        publish_passenger_status(db, ride)
        if next_offer:
            publish_driver_offer(db, next_offer)
        return DriverRideOfferDecisionResponse(ride_id=ride.id, ride_status=ride.status, message=message)

    def passenger_status(self, db: Session, ride: Ride) -> PassengerRideStatusResponse:
        driver = db.get(Driver, ride.driver_id) if ride.driver_id else None
        vehicle = db.get(Vehicle, ride.vehicle_id) if ride.vehicle_id else None
        quote = db.scalar(select(FareQuote).where(FareQuote.ride_id == ride.id).order_by(FareQuote.created_at.desc()))
        if ride.status == 'driver_arriving':
            message = 'Your Driver is on the way.'
        elif ride.status == 'driver_arrived':
            message = 'Your Driver has arrived at the pickup location.'
        elif ride.status == 'in_progress':
            message = 'Your ride is in progress.'
        elif ride.status == 'completed':
            message = 'You have reached your destination.'
        elif ride.status == 'cancelled' and ride.cancelled_by:
            message = f'This ride was ended by the {ride.cancelled_by}.'
        elif ride.status == 'cancelled' and ride.cancellation_reason == 'no_eligible_driver':
            message = 'No nearby verified Driver is available right now. Please try again shortly.'
        elif ride.status == 'searching':
            message = 'Finding a nearby Driver for you.'
        else:
            message = 'Your ride status has been updated.'
        location = db.get(DriverCurrentLocation, ride.driver_id) if ride.driver_id else None
        arrival = None
        if location and ride.status in {'driver_arriving', 'driver_arrived'}:
            distance = self._distance_km(float(location.latitude), float(location.longitude), float(ride.pickup_latitude), float(ride.pickup_longitude))
            arrival = 0 if ride.status == 'driver_arrived' else max(1, round(distance / 25 * 60))
        return PassengerRideStatusResponse(
            ride_id=ride.id, status=ride.status, message=message,
            pickup_address=ride.pickup_address, destination_address=ride.destination_address,
            fare_paise=quote.amount_paise if quote else 0,
            driver_name=driver.full_name if driver else None,
            vehicle_name=f'{vehicle.make} {vehicle.model}' if vehicle else None,
            vehicle_registration_number=vehicle.registration_number if vehicle else None,
            driver_arrival_minutes=arrival,
            pickup_latitude=float(ride.pickup_latitude), pickup_longitude=float(ride.pickup_longitude),
            destination_latitude=float(ride.destination_latitude), destination_longitude=float(ride.destination_longitude),
            driver_latitude=float(location.latitude) if location else None,
            driver_longitude=float(location.longitude) if location else None,
            driver_heading_degrees=location.heading_degrees if location else None,
            route_geojson=ride.route_geojson,
            can_cancel=ride.status in {'requested', 'searching', 'driver_assigned', 'driver_arriving', 'driver_arrived'},
            can_end=ride.status == 'in_progress',
            ride_start_otp=RideLifecycleService._ride_start_otp(db.get(Passenger, ride.passenger_id)) if ride.status == 'driver_arrived' else None,
            cancellation_reason=ride.cancellation_reason if ride.status == 'cancelled' else None,
        )

    def update_driver_location(self, db: Session, driver: Driver, latitude: float, longitude: float, heading_degrees: int | None, accuracy_meters: float | None = None, speed_mps: float | None = None, recorded_at: datetime | None = None) -> None:
        ride = db.scalar(select(Ride).where(
            Ride.driver_id == driver.id,
            Ride.status.in_(('driver_arriving', 'driver_arrived', 'in_progress')),
        ))
        if not driver.is_online and not ride:
            raise HTTPException(status_code=409, detail='Go online before sharing your Driver location.')
        now = datetime.now(UTC)
        captured_at = recorded_at or now
        if captured_at.tzinfo is None:
            captured_at = captured_at.replace(tzinfo=UTC)
        if abs((now - captured_at).total_seconds()) > 120:
            raise HTTPException(status_code=422, detail='Location reading is stale. Wait for a fresh GPS signal.')
        if accuracy_meters is not None and accuracy_meters > 150:
            raise HTTPException(status_code=422, detail='Location accuracy is too low. Move to an open area and try again.')
        location = db.get(DriverCurrentLocation, driver.id)
        if location:
            previous_at = location.recorded_at.replace(tzinfo=UTC) if location.recorded_at.tzinfo is None else location.recorded_at
            elapsed = max(1, (captured_at - previous_at).total_seconds())
            implied_speed = self._distance_km(float(location.latitude), float(location.longitude), latitude, longitude) * 1000 / elapsed
            if elapsed < 120 and implied_speed > 55:
                raise HTTPException(status_code=422, detail='Location jump was rejected. Wait for GPS to stabilize.')
            location.latitude, location.longitude = latitude, longitude
            location.heading_degrees, location.recorded_at = heading_degrees, captured_at
            location.accuracy_meters, location.speed_mps = accuracy_meters, speed_mps
        else:
            location = DriverCurrentLocation(driver_id=driver.id, latitude=latitude, longitude=longitude, heading_degrees=heading_degrees, accuracy_meters=accuracy_meters, speed_mps=speed_mps, recorded_at=captured_at)
            db.add(location)
        db.commit()
        if ride:
            publish_driver_location(ride.passenger_id, ride.id, {
                'ride_id': ride.id, 'latitude': latitude, 'longitude': longitude,
                'heading_degrees': heading_degrees, 'accuracy_meters': accuracy_meters,
                'recorded_at': captured_at.isoformat(),
            })

    def expire_offer(self, db: Session, offer_id: int) -> tuple[RideDispatchOffer, Ride, RideDispatchOffer | None] | None:
        offer = db.get(RideDispatchOffer, offer_id)
        if not offer or offer.status != 'pending' or not self._is_expired(offer, datetime.now(UTC)):
            return None
        ride = db.get(Ride, offer.ride_id)
        next_offer = self._expire_and_retry(db, offer)
        db.commit()
        if not ride:
            return None
        db.refresh(ride)
        return offer, ride, next_offer

    def _expire_and_retry(self, db: Session, offer: RideDispatchOffer) -> RideDispatchOffer | None:
        offer.status, offer.responded_at = 'expired', datetime.now(UTC)
        ride = db.get(Ride, offer.ride_id)
        if ride and ride.status == 'searching':
            db.add(RideEvent(ride_id=ride.id, actor_type='system', actor_id=None, event_type='ride_offer_expired', payload={'offer_id': offer.id}))
            return self.dispatch(db, ride)
        return None

    def _nearest_candidate(self, db: Session, ride: Ride, excluded_driver_ids: set[int]) -> tuple[Driver, float] | None:
        category = db.get(RideCategory, ride.category_id)
        if not category:
            return None
        # Reconcile legacy fully-approved accounts before applying the active
        # status filter. This is idempotent and never activates unverified data.
        pending_online = db.scalars(select(Driver).where(
            Driver.is_online.is_(True), Driver.status == 'pending',
        )).all()
        for pending_driver in pending_online:
            self.readiness_service.reconcile(db, pending_driver)

        rows = db.execute(select(Driver, DriverCurrentLocation).outerjoin(
            DriverCurrentLocation, DriverCurrentLocation.driver_id == Driver.id,
        ).join(
            DriverVehicleAssignment, (DriverVehicleAssignment.driver_id == Driver.id) & DriverVehicleAssignment.ended_at.is_(None),
        ).join(
            Vehicle, Vehicle.id == DriverVehicleAssignment.vehicle_id,
        ).where(
            Driver.is_online.is_(True), Driver.status == 'active', Vehicle.verification_status == 'verified',
            Vehicle.category_code == category.code,
        )).all()
        candidates: list[tuple[Driver, float]] = []
        for driver, location in rows:
            vehicle = self._active_vehicle(db, driver.id)
            if not vehicle or driver.id in excluded_driver_ids:
                continue
            active_ride = db.scalar(select(Ride.id).where(
                Ride.driver_id == driver.id,
                Ride.status.in_(('driver_assigned', 'driver_arriving', 'driver_arrived', 'in_progress')),
            ).limit(1))
            if active_ride:
                continue
            if location:
                recorded_at = location.recorded_at.replace(tzinfo=UTC) if location.recorded_at.tzinfo is None else location.recorded_at
                if datetime.now(UTC) - recorded_at > timedelta(minutes=5):
                    location = None
            coordinates = self._driver_coordinates(driver, location)
            if not coordinates:
                continue
            distance = self._distance_km(coordinates[0], coordinates[1], float(ride.pickup_latitude), float(ride.pickup_longitude))
            if distance <= self.maximum_pickup_distance_km:
                candidates.append((driver, distance))
        return min(candidates, key=lambda item: item[1]) if candidates else None

    def _driver_coordinates(self, driver: Driver, location: DriverCurrentLocation | None) -> tuple[float, float] | None:
        if location:
            return float(location.latitude), float(location.longitude)
        city = (driver.operating_city or '').strip().casefold()
        return self.city_centres.get(city)

    @staticmethod
    def _active_vehicle(db: Session, driver_id: int) -> Vehicle | None:
        return db.scalar(select(Vehicle).join(DriverVehicleAssignment, DriverVehicleAssignment.vehicle_id == Vehicle.id).where(DriverVehicleAssignment.driver_id == driver_id, DriverVehicleAssignment.ended_at.is_(None)).order_by(DriverVehicleAssignment.started_at.desc()))

    @staticmethod
    def _distance_km(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
        lat_a, lon_a, lat_b, lon_b = map(radians, (latitude_a, longitude_a, latitude_b, longitude_b))
        value = sin((lat_b - lat_a) / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin((lon_b - lon_a) / 2) ** 2
        return 6371 * 2 * asin(sqrt(value))

    @staticmethod
    def _is_expired(offer: RideDispatchOffer, now: datetime) -> bool:
        expires_at = offer.expires_at.replace(tzinfo=UTC) if offer.expires_at.tzinfo is None else offer.expires_at
        return expires_at <= now
