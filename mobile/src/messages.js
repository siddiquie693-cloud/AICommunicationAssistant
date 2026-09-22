import { API_BASE_URL } from './config';
import {
  apiRequest,
  refreshAccessToken,
} from './api';

import { getAccessToken } from './storage';

export async function getMessages(
  token,
  conversationId
) {
  return apiRequest(
    `/api/conversations/${conversationId}/messages/`,
    {
      method: 'GET',
      token,
    }
  );
}

export async function createMessage(
  token,
  conversationId,
  content
) {
  return apiRequest(
    `/api/conversations/${conversationId}/messages/`,
    {
      method: 'POST',
      body: {
        content,
        sender_type: 'user',
      },
      token,
    }
  );
}

export async function updateMessage(
  token,
  conversationId,
  messageId,
  content
) {
  return apiRequest(
    `/api/conversations/${conversationId}/messages/${messageId}/`,
    {
      method: 'PATCH',
      body: {
        content,
      },
      token,
    }
  );
}

export async function deleteMessage(
  token,
  conversationId,
  messageId
) {
  return apiRequest(
    `/api/conversations/${conversationId}/messages/${messageId}/`,
    {
      method: 'DELETE',
      token,
    }
  );
}

async function performStreamRequest(
  accessToken,
  conversationId,
  content,
  preferredLanguage
) {
  return fetch(
    `${API_BASE_URL}/api/conversations/${conversationId}/messages/stream/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        content,
        preferred_language: preferredLanguage,
      }),
    }
  );
}

async function getStreamErrorMessage(
  response
) {
  let errorMessage = 'AI request failed.';

  try {
    const data = await response.json();

    errorMessage =
      data?.error?.message ||
      data?.detail ||
      errorMessage;
  } catch (error) {
    // Keep default error message.
  }

  return errorMessage;
}

export async function streamAIMessage(
  token,
  conversationId,
  content,
  preferredLanguage,
  onChunk
) {
  let accessToken =
    token || await getAccessToken();

  let response;

  try {
    response = await performStreamRequest(
      accessToken,
      conversationId,
      content,
      preferredLanguage
    );
  } catch (error) {
    throw error;
  }

  if (response.status === 401) {
    accessToken =
      await refreshAccessToken();

    response = await performStreamRequest(
      accessToken,
      conversationId,
      content,
      preferredLanguage
    );
  }

  if (!response.ok) {
    const errorMessage =
      await getStreamErrorMessage(response);

    throw new Error(errorMessage);
  }

  if (!response.body) {
    throw new Error(
      'Streaming response is not supported on this device.'
    );
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let completedText = '';

  while (true) {
    const { value, done } =
      await reader.read();

    if (done) {
      break;
    }

    const chunk = decoder.decode(value, {
      stream: true,
    });

    completedText += chunk;

    if (onChunk) {
      onChunk(chunk);
    }
  }

  const finalChunk = decoder.decode();

  if (finalChunk) {
    completedText += finalChunk;

    if (onChunk) {
      onChunk(finalChunk);
    }
  }

  if (
    completedText.trim() ===
    'AI service is temporarily unavailable. Please try again later.'
  ) {
    throw new Error(
      'AI service is temporarily unavailable. Please try again later.'
    );
  }

  if (!completedText.trim()) {
    throw new Error(
      'The AI returned an empty response. Please try again.'
    );
  }

  return completedText;
}