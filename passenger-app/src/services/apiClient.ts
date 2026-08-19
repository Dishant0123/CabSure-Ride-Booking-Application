import axios, { AxiosError, AxiosHeaders } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { environment } from '../config/environment';

export const PASSENGER_SESSION_KEY = '@cabapp/passenger-session';

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

const createRequestId = (): string =>
  `passenger-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

const toApiError = (error: unknown): ApiError => {
  if (!axios.isAxiosError(error)) {
    return new ApiError('An unexpected connection error occurred.');
  }

  const axiosError = error as AxiosError<{ detail?: string; message?: string }>;
  if (axiosError.code === 'ECONNABORTED') {
    return new ApiError('The request timed out. Please try again.');
  }

  if (!axiosError.response) {
    return new ApiError('Unable to reach the backend. Check your connection and try again.');
  }

  return new ApiError(
    axiosError.response.data?.detail ??
      axiosError.response.data?.message ??
      'The backend returned an unexpected error.',
    axiosError.response.status,
  );
};

export const apiClient = axios.create({
  baseURL: environment.apiBaseUrl,
  timeout: environment.apiTimeoutMs,
});

apiClient.interceptors.request.use(async (config) => {
  const headers = AxiosHeaders.from(config.headers);
  const savedSession = await AsyncStorage.getItem(PASSENGER_SESSION_KEY);
  let accessToken: string | undefined;
  try { accessToken = savedSession ? (JSON.parse(savedSession).access_token as string | undefined) : undefined; }
  catch { await AsyncStorage.removeItem(PASSENGER_SESSION_KEY); }
  headers.set('Accept', 'application/json');
  headers.set('X-Request-ID', createRequestId());
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
  config.headers = headers;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const apiError = toApiError(error);
    if (apiError.status === 401) await AsyncStorage.removeItem(PASSENGER_SESSION_KEY);
    return Promise.reject(apiError);
  },
);
