import { apiRequest } from './api';

export async function getConversations(
  token,
  {
    archived = false,
    search = '',
  } = {}
) {
  const params = new URLSearchParams();

  if (archived) {
    params.append('archived', 'true');
  }

  if (search.trim()) {
    params.append('search', search.trim());
  }

  const queryString = params.toString();

  const endpoint = queryString
    ? `/api/conversations/?${queryString}`
    : '/api/conversations/';

  return apiRequest(endpoint, {
    method: 'GET',
    token,
  });
}

export async function getTrashConversations(
  token,
  search = ''
) {
  const params = new URLSearchParams();

  if (search.trim()) {
    params.append('search', search.trim());
  }

  const queryString = params.toString();

  const endpoint = queryString
    ? `/api/conversations/trash/?${queryString}`
    : '/api/conversations/trash/';

  return apiRequest(endpoint, {
    method: 'GET',
    token,
  });
}

export async function createConversation(
  token,
  title
) {
  return apiRequest('/api/conversations/', {
    method: 'POST',
    body: {
      title,
    },
    token,
  });
}

export async function updateConversation(
  token,
  conversationId,
  updates
) {
  return apiRequest(
    `/api/conversations/${conversationId}/`,
    {
      method: 'PATCH',
      body: updates,
      token,
    }
  );
}

export async function archiveConversation(
  token,
  conversationId
) {
  return updateConversation(
    token,
    conversationId,
    {
      is_archived: true,
    }
  );
}

export async function unarchiveConversation(
  token,
  conversationId
) {
  return updateConversation(
    token,
    conversationId,
    {
      is_archived: false,
    }
  );
}

export async function deleteConversation(
  token,
  conversationId
) {
  return apiRequest(
    `/api/conversations/${conversationId}/`,
    {
      method: 'DELETE',
      token,
    }
  );
}

export async function restoreConversation(
  token,
  conversationId
) {
  return apiRequest(
    `/api/conversations/${conversationId}/restore/`,
    {
      method: 'POST',
      token,
    }
  );
}