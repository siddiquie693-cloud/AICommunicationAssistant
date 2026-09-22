import { API_BASE_URL } from './config';
import { notifySessionExpired } from './session';

import {
  getAccessToken,
  getRefreshToken,
  saveTokens,
  clearTokens,
} from './storage';

let refreshPromise = null;

const LOGIN_ENDPOINT = '/api/auth/login/';
const REFRESH_ENDPOINT = '/api/auth/refresh/';

function isAuthenticationEndpoint(endpoint) {
  return (
    endpoint === LOGIN_ENDPOINT ||
    endpoint === REFRESH_ENDPOINT
  );
}

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
      const refreshToken =
        await getRefreshToken();

      if (!refreshToken) {
        throw new Error(
          'Refresh token not found.'
        );
      }

      const response =
        await performRequest(
          REFRESH_ENDPOINT,
          {
            method: 'POST',
            body: {
              refresh: refreshToken,
            },
          }
        );

      const data =
        await parseResponse(response);

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

      const newRefreshToken =
        data?.refresh || refreshToken;

      await saveTokens(
        data.access,
        newRefreshToken
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

async function handleExpiredSession() {
  await clearTokens();

  notifySessionExpired();

  throw new Error(
    'Your session has expired. Please log in again.'
  );
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

  /*
   * Never attach a previously stored access token
   * to the login or refresh endpoints.
   */
  if (
    !isAuthenticationEndpoint(endpoint) &&
    !accessToken
  ) {
    accessToken = await getAccessToken();
  }

  let response = await performRequest(
    endpoint,
    {
      method,
      body,
      token:
        isAuthenticationEndpoint(endpoint)
          ? null
          : accessToken,
    }
  );

  const shouldRefresh =
    response.status === 401 &&
    !skipRefresh &&
    !isAuthenticationEndpoint(endpoint);

  if (shouldRefresh) {
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

    /*
     * The refresh succeeded, but the retried request
     * was still rejected. Treat the local session as
     * invalid rather than leaving stale credentials.
     */
    if (response.status === 401) {
      return handleExpiredSession();
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