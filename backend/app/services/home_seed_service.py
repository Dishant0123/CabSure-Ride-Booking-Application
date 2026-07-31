from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.ride_hailing import FareQuote, Ride, RideCategory, SavedPlace
from app.models.user import Passenger


class HomeSeedService:
    """Creates idempotent demo content for authenticated development accounts."""

    categories = (
        ('car', 'Car', 4, 18000, 4, 'car'),
        ('bike', 'Bike', 1, 8000, 6, 'motorbike'),
        ('auto', 'Auto', 3, 10000, 3, 'rickshaw'),
    )
    places = (
        ('Home', 'Vidyanagar, Hubballi, Karnataka', 15.3647, 75.1239),
        ('Work', 'IIT Dharwad, Karnataka', 15.4565, 74.9690),
    )

    def ensure(self, db: Session, passenger: Passenger) -> None:
        categories = self._ensure_categories(db)
        # Shop was a temporary third shortcut. Keep only the intentional Home/Work pair.
        db.execute(delete(SavedPlace).where(SavedPlace.passenger_id == passenger.id, SavedPlace.label == 'Shop'))
        existing_places = {item.label for item in db.scalars(select(SavedPlace).where(SavedPlace.passenger_id == passenger.id)).all()}
        db.add_all(
            SavedPlace(
                passenger_id=passenger.id,
                label=label,
                formatted_address=address,
                latitude=latitude,
                longitude=longitude,
            )
            for label, address, latitude, longitude in self.places
            if label not in existing_places
        )
        if not db.scalar(select(Ride.id).where(Ride.passenger_id == passenger.id).limit(1)):
            self._add_recent_rides(db, passenger.id, categories)
        db.commit()

    def _ensure_categories(self, db: Session) -> dict[str, RideCategory]:
        existing = {item.code: item for item in db.scalars(select(RideCategory)).all()}
        for code, name, seats, fare, eta, icon in self.categories:
            if code not in existing:
                item = RideCategory(
                    code=code,
                    display_name=name,
                    seat_count=seats,
                    base_fare_paise=fare,
                    estimated_arrival_minutes=eta,
                    icon_key=icon,
                )
                db.add(item)
                db.flush()
                existing[code] = item
        return existing

    def _add_recent_rides(self, db: Session, passenger_id: int, categories: dict[str, RideCategory]) -> None:
        now = datetime.now(UTC)
        rides = (
            ('Dharwad', 'Hubballi', 40 * 60, 20000, now - timedelta(days=2)),
            ('Belur', 'Hubballi', 55 * 60, 80000, now - timedelta(days=14)),
            ('Dharwad', 'Goa', 150 * 60, 800000, now - timedelta(days=30)),
        )
        for pickup, destination, duration, fare, completed_at in rides:
            ride = Ride(
                passenger_id=passenger_id,
                category_id=categories['car'].id,
                status='completed',
                pickup_address=pickup,
                pickup_latitude=15.3647,
                pickup_longitude=75.1239,
                destination_address=destination,
                destination_latitude=15.4909,
                destination_longitude=75.1240,
                requested_at=completed_at - timedelta(minutes=duration // 60),
                completed_at=completed_at,
                final_duration_seconds=duration,
            )
            db.add(ride)
            db.flush()
            db.add(FareQuote(ride_id=ride.id, amount_paise=fare, is_final=True))
