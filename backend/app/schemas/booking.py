from datetime import datetime

from pydantic import BaseModel, Field


class LocationOptionResponse(BaseModel):
    id: int
    name: str
    formatted_address: str
    latitude: float
    longitude: float


class RideEstimateRequest(BaseModel):
    pickup_location_id: int
    destination_location_id: int
    category_id: int


class UpdateSavedPlaceRequest(BaseModel):
    location_id: int = Field(gt=0)


class FareItemResponse(BaseModel):
    label: str
    amount_paise: int


class RideEstimateResponse(BaseModel):
    pickup: LocationOptionResponse
    destination: LocationOptionResponse
    category_name: str
    distance_km: float
    duration_minutes: int
    fare_paise: int
    fare_items: list[FareItemResponse]


class RideBookingResponse(BaseModel):
    ride_id: int
    status: str
    pickup_address: str
    destination_address: str
    fare_paise: int
    requested_at: datetime
