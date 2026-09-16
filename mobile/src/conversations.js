import { apiRequest } from './api';

export async function getConversations(token) {
  return apiRequest('/api/conversations/', {
    method: 'GET',
    token,
  });
}

export async function createConversation(token, title) {
  return apiRequest('/api/conversations/', {
    method: 'POST',
    body: {
      title,
    },
    token,
  });
}