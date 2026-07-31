from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TimestampedModel:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PassengerProfile(TimestampedModel, Base):
    __tablename__ = 'passenger_profiles'
    passenger_id: Mapped[int] = mapped_column(ForeignKey('passengers.id', ondelete='CASCADE'), primary_key=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    profile_photo_url: Mapped[str | None] = mapped_column(String(2048))
    preferred_language: Mapped[str] = mapped_column(String(10), default='en', nullable=False)
    accessibility_preferences: Mapped[dict | None] = mapped_column(JSON)


class Driver(TimestampedModel, Base):
    __tablename__ = 'drivers'
    __table_args__ = (CheckConstraint("status IN ('pending', 'active', 'suspended', 'deactivated')", name='ck_drivers_status'), Index('ix_drivers_status_city', 'status', 'operating_city'))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    status: Mapped[str] = mapped_column(String(20), default='pending', nullable=False)
    operating_city: Mapped[str | None] = mapped_column(String(120))
    profile_photo_url: Mapped[str | None] = mapped_column(String(2048))
    rating_average: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal('0.00'), nullable=False)
    completed_rides_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_online_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Vehicle(TimestampedModel, Base):
    __tablename__ = 'vehicles'
    __table_args__ = (UniqueConstraint('registration_number', name='uq_vehicles_registration_number'), CheckConstraint("verification_status IN ('pending', 'verified', 'rejected', 'expired')", name='ck_vehicles_verification_status'))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    registration_number: Mapped[str] = mapped_column(String(32), nullable=False)
    make: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str | None] = mapped_column(String(40))
    category_code: Mapped[str] = mapped_column(String(32), nullable=False)
    seat_count: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(20), default='pending', nullable=False)


class DriverVehicleAssignment(TimestampedModel, Base):
    __tablename__ = 'driver_vehicle_assignments'
    __table_args__ = (Index('ix_driver_vehicle_active', 'driver_id', 'ended_at'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey('drivers.id', ondelete='CASCADE'), nullable=False)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey('vehicles.id', ondelete='RESTRICT'), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DriverDocument(TimestampedModel, Base):
    __tablename__ = 'driver_documents'
    __table_args__ = (UniqueConstraint('driver_id', 'document_type', name='uq_driver_documents_type'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey('drivers.id', ondelete='CASCADE'), nullable=False)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(20), default='pending', nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SavedPlace(TimestampedModel, Base):
    __tablename__ = 'saved_places'
    __table_args__ = (UniqueConstraint('passenger_id', 'label', name='uq_saved_places_label'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    passenger_id: Mapped[int] = mapped_column(ForeignKey('passengers.id', ondelete='CASCADE'), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    formatted_address: Mapped[str] = mapped_column(String(512), nullable=False)
    google_place_id: Mapped[str | None] = mapped_column(String(255), index=True)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)


class LocationCatalog(TimestampedModel, Base):
    __tablename__ = 'location_catalog'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    formatted_address: Mapped[str] = mapped_column(String(512), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)


class EmergencyContact(TimestampedModel, Base):
    __tablename__ = 'emergency_contacts'
    __table_args__ = (UniqueConstraint('passenger_id', 'phone_number', name='uq_emergency_contact_phone'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    passenger_id: Mapped[int] = mapped_column(ForeignKey('passengers.id', ondelete='CASCADE'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    relationship: Mapped[str | None] = mapped_column(String(64))


class ServiceArea(TimestampedModel, Base):
    __tablename__ = 'service_areas'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), default='IN', nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    boundary_geojson: Mapped[dict] = mapped_column(JSON, nullable=False)


class RideCategory(TimestampedModel, Base):
    __tablename__ = 'ride_categories'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    seat_count: Mapped[int] = mapped_column(Integer, nullable=False)
    base_fare_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_arrival_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    icon_key: Mapped[str] = mapped_column(String(32), default='car', nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Ride(TimestampedModel, Base):
    __tablename__ = 'rides'
    __table_args__ = (CheckConstraint("status IN ('requested', 'searching', 'driver_assigned', 'driver_arriving', 'in_progress', 'completed', 'cancelled')", name='ck_rides_status'), Index('ix_rides_passenger_requested', 'passenger_id', 'requested_at'), Index('ix_rides_driver_status_requested', 'driver_id', 'status', 'requested_at'))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    passenger_id: Mapped[int] = mapped_column(ForeignKey('passengers.id', ondelete='RESTRICT'), nullable=False)
    driver_id: Mapped[int | None] = mapped_column(ForeignKey('drivers.id', ondelete='RESTRICT'))
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey('vehicles.id', ondelete='RESTRICT'))
    category_id: Mapped[int] = mapped_column(ForeignKey('ride_categories.id', ondelete='RESTRICT'), nullable=False)
    service_area_id: Mapped[int | None] = mapped_column(ForeignKey('service_areas.id', ondelete='RESTRICT'))
    status: Mapped[str] = mapped_column(String(24), default='requested', nullable=False)
    pickup_address: Mapped[str] = mapped_column(String(512), nullable=False)
    pickup_place_id: Mapped[str | None] = mapped_column(String(255))
    pickup_latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    pickup_longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    destination_address: Mapped[str] = mapped_column(String(512), nullable=False)
    destination_place_id: Mapped[str | None] = mapped_column(String(255))
    destination_latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    destination_longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancellation_reason: Mapped[str | None] = mapped_column(String(255))
    estimated_distance_meters: Mapped[int | None] = mapped_column(Integer)
    estimated_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    final_distance_meters: Mapped[int | None] = mapped_column(Integer)
    final_duration_seconds: Mapped[int | None] = mapped_column(Integer)


class RideStop(TimestampedModel, Base):
    __tablename__ = 'ride_stops'
    __table_args__ = (UniqueConstraint('ride_id', 'stop_order', name='uq_ride_stops_order'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ride_id: Mapped[int] = mapped_column(ForeignKey('rides.id', ondelete='CASCADE'), nullable=False)
    stop_order: Mapped[int] = mapped_column(Integer, nullable=False)
    address: Mapped[str] = mapped_column(String(512), nullable=False)
    google_place_id: Mapped[str | None] = mapped_column(String(255))
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)


class RideEvent(Base):
    __tablename__ = 'ride_events'
    __table_args__ = (Index('ix_ride_events_ride_occurred', 'ride_id', 'occurred_at'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ride_id: Mapped[int] = mapped_column(ForeignKey('rides.id', ondelete='CASCADE'), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class FareQuote(TimestampedModel, Base):
    __tablename__ = 'fare_quotes'
    __table_args__ = (Index('ix_fare_quotes_ride_created', 'ride_id', 'created_at'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ride_id: Mapped[int] = mapped_column(ForeignKey('rides.id', ondelete='CASCADE'), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default='INR', nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FareLineItem(Base):
    __tablename__ = 'fare_line_items'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fare_quote_id: Mapped[int] = mapped_column(ForeignKey('fare_quotes.id', ondelete='CASCADE'), nullable=False)
    item_type: Mapped[str] = mapped_column(String(48), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)


class Payment(TimestampedModel, Base):
    __tablename__ = 'payments'
    __table_args__ = (UniqueConstraint('provider', 'provider_payment_id', name='uq_payment_provider_reference'), Index('ix_payments_ride_status', 'ride_id', 'status'))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ride_id: Mapped[int] = mapped_column(ForeignKey('rides.id', ondelete='RESTRICT'), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default='INR', nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(64))
    provider_payment_id: Mapped[str | None] = mapped_column(String(255))
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)


class Rating(TimestampedModel, Base):
    __tablename__ = 'ratings'
    __table_args__ = (UniqueConstraint('ride_id', 'rater_type', name='uq_ratings_ride_rater'), CheckConstraint('score BETWEEN 1 AND 5', name='ck_ratings_score'))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ride_id: Mapped[int] = mapped_column(ForeignKey('rides.id', ondelete='CASCADE'), nullable=False)
    rater_type: Mapped[str] = mapped_column(String(16), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)


class DeviceSession(TimestampedModel, Base):
    __tablename__ = 'device_sessions'
    __table_args__ = (Index('ix_device_sessions_passenger_active', 'passenger_id', 'revoked_at', 'expires_at'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    passenger_id: Mapped[int] = mapped_column(ForeignKey('passengers.id', ondelete='CASCADE'), nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    device_id: Mapped[str | None] = mapped_column(String(255))
    platform: Mapped[str | None] = mapped_column(String(32))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class DriverCurrentLocation(Base):
    __tablename__ = 'driver_current_locations'
    driver_id: Mapped[int] = mapped_column(ForeignKey('drivers.id', ondelete='CASCADE'), primary_key=True)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    heading_degrees: Mapped[int | None] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)


class Notification(TimestampedModel, Base):
    __tablename__ = 'notifications'
    __table_args__ = (Index('ix_notifications_passenger_read_created', 'passenger_id', 'read_at', 'created_at'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    passenger_id: Mapped[int] = mapped_column(ForeignKey('passengers.id', ondelete='CASCADE'), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    data_json: Mapped[dict | None] = mapped_column(JSON)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SupportTicket(TimestampedModel, Base):
    __tablename__ = 'support_tickets'
    __table_args__ = (Index('ix_support_tickets_passenger_status', 'passenger_id', 'status'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    passenger_id: Mapped[int] = mapped_column(ForeignKey('passengers.id', ondelete='RESTRICT'), nullable=False)
    ride_id: Mapped[int | None] = mapped_column(ForeignKey('rides.id', ondelete='SET NULL'))
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default='open', nullable=False)
    subject: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    __table_args__ = (Index('ix_audit_logs_entity_occurred', 'entity_type', 'entity_id', 'occurred_at'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_type: Mapped[str | None] = mapped_column(String(32))
    actor_id: Mapped[int | None] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(96), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class OutboxEvent(Base):
    __tablename__ = 'outbox_events'
    __table_args__ = (Index('ix_outbox_events_unpublished_created', 'published_at', 'created_at'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(96), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
