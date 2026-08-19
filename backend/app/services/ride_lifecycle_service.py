from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ride_hailing import Driver, FareLineItem, FareQuote, Rating, Ride, RideDispatchOffer, RideEvent
from app.models.user import Passenger
from app.schemas.booking import FareSummaryItemResponse, DriverActiveRideResponse, RideMutationResponse, RideRatingResponse, RideSummaryResponse
from app.services.realtime_events import publish_driver_ride_event, publish_passenger_status


ACTIVE_STATUSES = ('requested', 'searching', 'driver_assigned', 'driver_arriving', 'driver_arrived', 'in_progress')
PASSENGER_CANCEL_REASONS = {'changed_plans', 'driver_delay', 'wrong_pickup', 'safety_concern', 'emergency', 'other'}
DRIVER_CANCEL_REASONS = {'vehicle_issue', 'passenger_no_show', 'safety_concern', 'emergency', 'other'}


class RideLifecycleService:
    def passenger_active(self, db: Session, passenger: Passenger) -> Ride | None:
        return db.scalar(select(Ride).where(
            Ride.passenger_id == passenger.id, Ride.status.in_(ACTIVE_STATUSES),
        ).order_by(Ride.requested_at.desc()))

    def driver_active(self, db: Session, driver: Driver) -> Ride | None:
        return db.scalar(select(Ride).where(
            Ride.driver_id == driver.id, Ride.status.in_(ACTIVE_STATUSES),
        ).order_by(Ride.requested_at.desc()))

    def driver_snapshot(self, db: Session, driver: Driver) -> DriverActiveRideResponse | None:
        ride = self.driver_active(db, driver)
        if not ride:
            return None
        passenger = db.get(Passenger, ride.passenger_id)
        return DriverActiveRideResponse(
            ride_id=ride.id, status=ride.status, pickup_address=ride.pickup_address,
            destination_address=ride.destination_address,
            pickup_latitude=float(ride.pickup_latitude), pickup_longitude=float(ride.pickup_longitude),
            destination_latitude=float(ride.destination_latitude), destination_longitude=float(ride.destination_longitude),
            passenger_name=passenger.full_name if passenger else 'Passenger', route_geojson=ride.route_geojson,
            can_cancel=ride.status in {'driver_arriving', 'driver_arrived'}, can_end=ride.status == 'in_progress',
        )

    def cancel_by_passenger(self, db: Session, passenger: Passenger, ride_id: int, reason: str, confirm: bool) -> RideMutationResponse:
        ride = db.scalar(select(Ride).where(Ride.id == ride_id, Ride.passenger_id == passenger.id))
        if not ride:
            raise HTTPException(status_code=404, detail='Ride was not found.')
        if not confirm:
            raise HTTPException(status_code=400, detail='Confirm cancellation before ending this ride.')
        if ride.status not in ACTIVE_STATUSES:
            raise HTTPException(status_code=409, detail='This ride is no longer active.')
        if reason not in PASSENGER_CANCEL_REASONS:
            raise HTTPException(status_code=422, detail='Choose a valid passenger cancellation reason.')
        if ride.status == 'in_progress' and reason not in {'safety_concern', 'emergency'}:
            raise HTTPException(status_code=409, detail='An in-progress ride can only be ended for safety or an emergency. Contact support for other issues.')
        event = 'trip_ended_by_passenger' if ride.status == 'in_progress' else 'ride_cancelled_by_passenger'
        self._cancel(db, ride, 'passenger', reason, event, passenger.id)
        return RideMutationResponse(ride_id=ride.id, status=ride.status, message='Your ride has been ended.' if event.startswith('trip_ended') else 'Your ride has been cancelled.')

    def cancel_by_driver(self, db: Session, driver: Driver, ride_id: int, reason: str, confirm: bool) -> RideMutationResponse:
        ride = db.scalar(select(Ride).where(Ride.id == ride_id, Ride.driver_id == driver.id))
        if not ride:
            raise HTTPException(status_code=404, detail='Active ride was not found.')
        if not confirm:
            raise HTTPException(status_code=400, detail='Confirm before ending this ride.')
        if ride.status not in {'driver_arriving', 'driver_arrived', 'in_progress'}:
            raise HTTPException(status_code=409, detail='This ride cannot be ended from its current state.')
        if reason not in DRIVER_CANCEL_REASONS:
            raise HTTPException(status_code=422, detail='Choose a valid Driver cancellation reason.')
        if ride.status == 'in_progress' and reason not in {'vehicle_issue', 'safety_concern', 'emergency'}:
            raise HTTPException(status_code=409, detail='An in-progress ride can only be ended for a vehicle issue, safety concern, or emergency.')
        event = 'trip_ended_by_driver' if ride.status == 'in_progress' else 'ride_cancelled_by_driver'
        self._cancel(db, ride, 'driver', reason, event, driver.id)
        return RideMutationResponse(ride_id=ride.id, status=ride.status, message='The ride has been ended and the passenger was notified.')

    def action(self, db: Session, driver: Driver, ride_id: int, action: str, start_otp: str | None = None) -> RideMutationResponse:
        ride = db.scalar(select(Ride).where(Ride.id == ride_id, Ride.driver_id == driver.id))
        if not ride:
            raise HTTPException(status_code=404, detail='Active ride was not found.')
        transitions = {
            ('driver_arriving', 'arrived'): ('driver_arrived', 'Driver reached pickup'),
            ('driver_arrived', 'start'): ('in_progress', 'Trip started'),
            ('in_progress', 'complete'): ('completed', 'Trip completed'),
        }
        transition = transitions.get((ride.status, action))
        if not transition:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='This ride action is not available right now.')
        if action == 'start':
            passenger = db.get(Passenger, ride.passenger_id)
            expected = self._ride_start_otp(passenger)
            if not start_otp or start_otp != expected:
                raise HTTPException(status_code=422, detail='The ride-start OTP is incorrect. Ask the passenger for the 4-digit OTP shown in their app.')
        ride.status = transition[0]
        now = datetime.now(UTC)
        if action == 'start':
            ride.started_at = now
        elif action == 'complete':
            ride.completed_at = now
            ride.final_distance_meters = ride.estimated_distance_meters
            ride.final_duration_seconds = max(1, round((now - self._aware(ride.started_at or now)).total_seconds()))
            quote = db.scalar(select(FareQuote).where(FareQuote.ride_id == ride.id).order_by(FareQuote.created_at.desc()))
            if quote:
                quote.is_final = True
            driver.completed_rides_count += 1
        db.add(RideEvent(ride_id=ride.id, actor_type='driver', actor_id=driver.id, event_type=f'ride_{action}', payload=None))
        db.commit(); db.refresh(ride)
        publish_passenger_status(db, ride)
        publish_driver_ride_event(driver.id, ride, f'ride.{ride.status}')
        return RideMutationResponse(ride_id=ride.id, status=ride.status, message=transition[1])

    def summary(self, db: Session, ride: Ride, rater_type: str) -> RideSummaryResponse:
        if ride.status != 'completed':
            raise HTTPException(status_code=409, detail='Fare summary is available after ride completion.')
        quote = db.scalar(select(FareQuote).where(FareQuote.ride_id == ride.id, FareQuote.is_final.is_(True)).order_by(FareQuote.created_at.desc()))
        items = db.scalars(select(FareLineItem).where(FareLineItem.fare_quote_id == quote.id).order_by(FareLineItem.id)).all() if quote else []
        ratings = set(db.scalars(select(Rating.rater_type).where(Rating.ride_id == ride.id)).all())
        return RideSummaryResponse(
            ride_id=ride.id, status=ride.status, pickup_address=ride.pickup_address, destination_address=ride.destination_address,
            distance_km=round((ride.final_distance_meters or ride.estimated_distance_meters or 0) / 1000, 1),
            duration_minutes=max(1, round((ride.final_duration_seconds or ride.estimated_duration_seconds or 0) / 60)),
            fare_paise=quote.amount_paise if quote else 0,
            fare_items=[FareSummaryItemResponse(label=item.item_type.replace('_', ' ').title(), amount_paise=item.amount_paise) for item in items],
            passenger_rating_submitted='passenger' in ratings, driver_rating_submitted='driver' in ratings,
        )

    def rate(self, db: Session, ride: Ride, rater_type: str, score: int, comment: str | None) -> RideRatingResponse:
        if ride.status != 'completed':
            raise HTTPException(status_code=409, detail='Ratings are available after ride completion.')
        if db.scalar(select(Rating).where(Rating.ride_id == ride.id, Rating.rater_type == rater_type)):
            raise HTTPException(status_code=409, detail='You already rated this ride.')
        db.add(Rating(ride_id=ride.id, rater_type=rater_type, score=score, comment=comment.strip() if comment else None))
        db.flush()
        if rater_type == 'passenger' and ride.driver_id:
            values = db.scalars(select(Rating.score).join(Ride, Ride.id == Rating.ride_id).where(Rating.rater_type == 'passenger', Ride.driver_id == ride.driver_id)).all()
            driver = db.get(Driver, ride.driver_id)
            if driver and values:
                driver.rating_average = round(sum(values) / len(values), 2)
        db.commit()
        return RideRatingResponse(ride_id=ride.id, score=score, message='Thank you. Your rating was submitted.')

    @staticmethod
    def _ride_start_otp(passenger: Passenger | None) -> str:
        digits = ''.join(character for character in (passenger.phone_number if passenger else '') if character.isdigit())
        if len(digits) < 4:
            raise HTTPException(status_code=409, detail='Passenger phone verification is incomplete.')
        return digits[-4:]

    @staticmethod
    def _cancel(db: Session, ride: Ride, actor: str, reason: str, event: str, actor_id: int) -> None:
        driver_id = ride.driver_id
        ride.status, ride.cancelled_at = 'cancelled', datetime.now(UTC)
        ride.cancelled_by, ride.cancellation_reason = actor, reason.strip()
        db.add(RideEvent(ride_id=ride.id, actor_type=actor, actor_id=actor_id, event_type=event, payload={'reason': reason.strip()}))
        pending = db.scalars(select(RideDispatchOffer).where(RideDispatchOffer.ride_id == ride.id, RideDispatchOffer.status == 'pending')).all()
        for offer in pending:
            offer.status, offer.responded_at = 'cancelled', datetime.now(UTC)
        db.commit(); db.refresh(ride)
        publish_passenger_status(db, ride)
        if driver_id:
            publish_driver_ride_event(driver_id, ride, 'ride.cancelled')

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value
