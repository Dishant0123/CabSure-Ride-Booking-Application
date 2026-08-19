from datetime import datetime

import pytest
from fastapi import HTTPException

from app.services.booking_service import BookingService
from app.services.map_provider_service import MapProviderService


def test_service_area_accepts_dharwad_and_hubballi_locations() -> None:
    service = MapProviderService()

    assert service.contains(15.4589, 75.0078)
    assert service.contains(15.3518, 75.1379)


def test_service_area_rejects_locations_beyond_150_km() -> None:
    service = MapProviderService()

    with pytest.raises(HTTPException) as error:
        service.ensure_in_service_area(12.9716, 77.5946)

    assert error.value.status_code == 422


@pytest.mark.parametrize(('hour', 'expected'), [(0, True), (4, True), (5, False), (21, False), (22, True)])
def test_night_charge_window(hour: int, expected: bool) -> None:
    assert BookingService._is_night(datetime(2026, 8, 13, hour, 0)) is expected
