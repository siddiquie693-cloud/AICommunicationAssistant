const DEFAULT_API_BASE_URL =
  'http://10.145.219.95:8000';

const configuredApiBaseUrl =
  process.env.EXPO_PUBLIC_API_BASE_URL ||
  (__DEV__ ? DEFAULT_API_BASE_URL : null);

if (!configuredApiBaseUrl) {
  throw new Error(
    'EXPO_PUBLIC_API_BASE_URL is required for production builds.'
  );
}

export const API_BASE_URL =
  configuredApiBaseUrl.replace(/\/+$/, '');

export function validateApiConfiguration() {
  const isHttps =
    API_BASE_URL.startsWith('https://');

  const isLocalDevelopment =
    API_BASE_URL.startsWith(
      'http://localhost'
    ) ||
    API_BASE_URL.startsWith(
      'http://127.0.0.1'
    ) ||
    API_BASE_URL.startsWith(
      'http://10.'
    ) ||
    API_BASE_URL.startsWith(
      'http://192.168.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.16.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.17.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.18.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.19.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.20.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.21.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.22.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.23.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.24.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.25.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.26.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.27.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.28.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.29.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.30.'
    ) ||
    API_BASE_URL.startsWith(
      'http://172.31.'
    );

  if (
    !isHttps &&
    !__DEV__ &&
    !isLocalDevelopment
  ) {
    throw new Error(
      'Production API must use HTTPS.'
    );
  }

  return {
    apiBaseUrl: API_BASE_URL,
    secureTransport:
      isHttps || isLocalDevelopment,
  };
}

validateApiConfiguration();