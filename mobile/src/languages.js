import { apiRequest } from './api';

export async function getLanguages() {
  return apiRequest('/api/auth/languages/', {
    method: 'GET',
  });
}