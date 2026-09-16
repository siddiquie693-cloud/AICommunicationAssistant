import { API_BASE_URL } from './config';

export async function apiRequest(
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

  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data?.error?.message ||
      data?.detail ||
      'API request failed.'
    );
  }

  return data;
}