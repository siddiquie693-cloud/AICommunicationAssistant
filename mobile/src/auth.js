import { apiRequest } from './api';
import { clearTokens } from './storage';

export async function login(
  username,
  password
) {
  return apiRequest('/api/auth/login/', {
    method: 'POST',
    body: {
      username,
      password,
    },
  });
}

export async function getCurrentUser(token) {
  return apiRequest('/api/auth/me/', {
    method: 'GET',
    token,
  });
}

export async function logout(
  accessToken,
  refreshToken
) {
  try {
    return await apiRequest(
      '/api/auth/logout/',
      {
        method: 'POST',
        body: {
          refresh: refreshToken,
        },
        token: accessToken,
      }
    );
  } finally {
    await clearTokens();
  }
}