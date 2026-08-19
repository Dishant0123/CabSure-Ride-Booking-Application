from math import asin, cos, radians, sin, sqrt
from urllib.parse import quote

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas.maps import GeocodedPlaceResponse, MapConfigResponse, RouteResponse


class MapProviderService:
    center_latitude = 15.3926
    center_longitude = 75.0833
    service_radius_km = 150.0
    bounds = [73.68, 14.04, 76.49, 16.74]
    api_base = 'https://api.geoapify.com/v1'

    def config(self) -> MapConfigResponse:
        key = self._key()
        return MapConfigResponse(
            style_url=f'https://maps.geoapify.com/v1/styles/klokantech-basic/style.json?apiKey={quote(key)}',
            attribution='© OpenStreetMap contributors · Geoapify',
            service_area=self.bounds,
            service_center=[self.center_longitude, self.center_latitude],
            service_radius_km=self.service_radius_km,
        )

    def search(self, query: str, outstation: bool = False) -> list[GeocodedPlaceResponse]:
        params = {
            'text': query,
            'format': 'json',
            'lang': 'en',
            'limit': 8,
            'filter': 'countrycode:in' if outstation else f'circle:{self.center_longitude},{self.center_latitude},{round(self.service_radius_km * 1000)}|countrycode:in',
            'bias': 'proximity:75.0833,15.3926',
            'apiKey': self._key(),
        }
        payload = self._get('/geocode/autocomplete', params)
        places = [self._place(item) for item in payload.get('results', []) if item.get('lat') is not None and item.get('lon') is not None and (outstation or self.contains(float(item['lat']), float(item['lon'])))]
        unique: dict[str, GeocodedPlaceResponse] = {}
        for place in places:
            unique.setdefault(place.place_id, place)
        return list(unique.values())

    def reverse(self, latitude: float, longitude: float, outstation: bool = False) -> GeocodedPlaceResponse:
        if not outstation:
            self.ensure_in_service_area(latitude, longitude)
        payload = self._get('/geocode/reverse', {
            'lat': latitude, 'lon': longitude, 'format': 'json', 'lang': 'en',
            'apiKey': self._key(),
        })
        results = payload.get('results', [])
        if not results:
            raise HTTPException(status_code=404, detail='No address was found at this map position.')
        if outstation and str(results[0].get('country_code', '')).lower() != 'in':
            raise HTTPException(status_code=422, detail='Outstation locations must be within India.')
        return self._place(results[0])

    def ensure_in_service_area(self, latitude: float, longitude: float) -> None:
        if not self.contains(latitude, longitude):
            raise HTTPException(status_code=422, detail='Choose a location within 150 km of Dharwad–Hubballi.')

    def contains(self, latitude: float, longitude: float) -> bool:
        lat1, lon1, lat2, lon2 = map(radians, (self.center_latitude, self.center_longitude, latitude, longitude))
        delta_lat, delta_lon = lat2 - lat1, lon2 - lon1
        value = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        return 6371.0 * 2 * asin(sqrt(value)) <= self.service_radius_km

    def route(self, origin: tuple[float, float], destination: tuple[float, float]) -> RouteResponse:
        payload = self._get('/routing', {
            'waypoints': f'{origin[0]},{origin[1]}|{destination[0]},{destination[1]}',
            'mode': 'drive', 'traffic': 'approximated', 'format': 'geojson',
            'apiKey': self._key(),
        })
        features = payload.get('features', [])
        if not features:
            raise HTTPException(status_code=422, detail='A drivable route could not be calculated for these locations.')
        feature = features[0]
        properties = feature.get('properties', {})
        return RouteResponse(
            distance_meters=round(float(properties.get('distance', 0))),
            duration_seconds=max(1, round(float(properties.get('time', 0)))),
            geometry=feature.get('geometry', {}),
            toll_fare_paise=0,
        )

    def _get(self, path: str, params: dict) -> dict:
        try:
            response = httpx.get(
                f'{self.api_base}{path}', params=params, timeout=8.0,
                headers={'User-Agent': f'CabSure/0.1 ({get_settings().maps_contact_email})'},
            )
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Map search is temporarily unavailable. Please try again.',
            ) from exc

    @staticmethod
    def _place(item: dict) -> GeocodedPlaceResponse:
        address = item.get('formatted') or item.get('address_line2') or item.get('name') or 'Selected location'
        name = item.get('name') or item.get('address_line1') or address.split(',')[0]
        place_id = item.get('place_id') or f"geoapify:{item.get('lat')}:{item.get('lon')}"
        return GeocodedPlaceResponse(
            place_id=str(place_id), name=str(name), formatted_address=str(address),
            latitude=float(item['lat']), longitude=float(item['lon']),
        )

    @staticmethod
    def _key() -> str:
        key = get_settings().geoapify_api_key
        if not key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Map services are not configured. Add GEOAPIFY_API_KEY to the backend environment.',
            )
        return key
