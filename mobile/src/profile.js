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