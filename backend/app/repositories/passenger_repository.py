from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ride_hailing import PassengerProfile
from app.models.user import Passenger


class PassengerRepository:
    def get_by_phone(self, db: Session, phone_number: str) -> Passenger | None:
        return db.scalar(select(Passenger).where(Passenger.phone_number == phone_number))

    def get_verified_by_phone(self, db: Session, phone_number: str) -> Passenger | None:
        return db.scalar(
            select(Passenger).where(
                Passenger.phone_number == phone_number,
                Passenger.is_phone_verified.is_(True),
                Passenger.status == 'active',
            )
        )

    def get_by_firebase_uid(self, db: Session, firebase_uid: str) -> Passenger | None:
        return db.scalar(select(Passenger).where(Passenger.firebase_uid == firebase_uid))

    def get_profile(self, db: Session, passenger_id: int) -> PassengerProfile | None:
        return db.get(PassengerProfile, passenger_id)

    def create_profile(self, db: Session, passenger_id: int) -> PassengerProfile:
        profile = PassengerProfile(passenger_id=passenger_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    def create(self, db: Session, passenger: Passenger) -> Passenger:
        db.add(passenger)
        db.commit()
        db.refresh(passenger)
        return passenger

    def save(self, db: Session, passenger: Passenger) -> Passenger:
        db.add(passenger)
        db.commit()
        db.refresh(passenger)
        return passenger
