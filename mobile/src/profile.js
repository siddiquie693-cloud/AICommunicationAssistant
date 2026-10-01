import { apiRequest } from './api';

export async function getProfile(token) {
  return apiRequest('/api/auth/profile/', {
    method: 'GET',
    token,
  });
}

export async function updateProfile(token, updates) {
  return apiRequest('/api/auth/profile/', {
    method: 'PATCH',
    body: updates,
    token,
  });
}

export async function getNIRAPersonalProfile(token) {
  return apiRequest('/api/auth/nira-profile/', {
    method: 'GET',
    token,
  });
}

export async function updateNIRAPersonalProfile(
  token,
  updates
) {
  return apiRequest('/api/auth/nira-profile/', {
    method: 'PATCH',
    body: updates,
    token,
  });
}