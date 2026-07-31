import { apiClient } from '../../../services/apiClient';

export type LocationOption = { id: number; name: string; formatted_address: string; latitude: number; longitude: number };
export type FareEstimate = { pickup: LocationOption; destination: LocationOption; category_name: string; distance_km: number; duration_minutes: number; fare_paise: number; fare_items: { label: string; amount_paise: number }[] };
export type RideBooking = { ride_id: number; status: string; pickup_address: string; destination_address: string; fare_paise: number; requested_at: string };

export const bookingApi = {
  locations: async () => (await apiClient.get<LocationOption[]>('/api/v1/passengers/me/locations')).data,
  estimate: async (pickup_location_id: number, destination_location_id: number, category_id: number) => (await apiClient.post<FareEstimate>('/api/v1/passengers/me/ride-estimates', { pickup_location_id, destination_location_id, category_id })).data,
  book: async (pickup_location_id: number, destination_location_id: number, category_id: number) => (await apiClient.post<RideBooking>('/api/v1/passengers/me/rides', { pickup_location_id, destination_location_id, category_id })).data,
  updateSavedPlace: async (savedPlaceId: number, locationId: number) => (await apiClient.patch(`/api/v1/passengers/me/saved-places/${savedPlaceId}`, { location_id: locationId })).data,
};
