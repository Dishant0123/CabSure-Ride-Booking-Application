import Config from 'react-native-config';

const DEFAULT_API_BASE_URL = 'http://10.0.2.2:8000';

export const environment = {
  apiBaseUrl: (Config.API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/$/, ''),
  apiTimeoutMs: 10_000,
  wsBaseUrl: (Config.WS_BASE_URL ?? (Config.API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/^http/, 'ws')).replace(/\/$/, ''),
} as const;
