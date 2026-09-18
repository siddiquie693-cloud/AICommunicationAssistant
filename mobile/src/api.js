import { API_BASE_URL } from './config';
import { notifySessionExpired } from './session';
import {
  getAccessToken,
  getRefreshToken,
  saveTokens,
  clearTokens,
} from './storage';

let refreshPromise = null;

async function parseResponse(response) {
  const responseText = await response.text();

  let data = null;

  if (responseText) {
    try {
      data = JSON.parse(responseText);
    } catch (error) {
      data = responseText;
    }
  }

  return data;
}

async function performRequest(
  endpoint,
  {
    method = 'GET',
    body = null,
    token = null,
  } = {}
) {
  const headers = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      method,
      headers,
      body: body
        ? JSON.stringify(body)
        : undefined,
    }
  );
}

async function refreshAccessTokenOnce() {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const refreshToken = await getRefreshToken();

      if (!refreshToken) {
        throw new Error(
          'Refresh token not found.'
        );
      }

      const response = await performRequest(
        '/api/auth/refresh/',
        {
          method: 'POST',
          body: {
            refresh: refreshToken,
          },
        }
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(
          data?.detail ||
          'Unable to refresh access token.'
        );
      }

      if (!data?.access) {
        throw new Error(
          'Unable to refresh access token.'
        );
      }

      await saveTokens(
        data.access,
        refreshToken
      );

      return data.access;
    } catch (error) {
      await clearTokens();
      throw error;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function apiRequest(
  endpoint,
  {
    method = 'GET',
    body = null,
    token = null,
    skipRefresh = false,
  } = {}
) {
  let accessToken = token;

  if (!accessToken) {
    accessToken = await getAccessToken();
  }

  let response = await performRequest(
    endpoint,
    {
      method,
      body,
      token: accessToken,
    }
  );

  if (
    response.status === 401 &&
    !skipRefresh &&
    endpoint !== '/api/auth/login/' &&
    endpoint !== '/api/auth/refresh/'
  ) {
    try {
      const newAccessToken =
        await refreshAccessTokenOnce();

      response = await performRequest(
        endpoint,
        {
          method,
          body,
          token: newAccessToken,
        }
      );
    } catch (error) {
      await clearTokens();

      notifySessionExpired();
      throw new Error(
        'Your session has expired. Please log in again.'
      );
    }
  }

  const data = await parseResponse(response);

  if (!response.ok) {
    throw new Error(
      data?.error?.message ||
      data?.detail ||
      'API request failed.'
    );
  }

  return data;
}