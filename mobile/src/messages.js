import { apiRequest } from './api';
import { API_BASE_URL } from './config';

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

export async function streamAIMessage(
  token,
  conversationId,
  content,
  onChunk
) {
  const response = await fetch(
    `${API_BASE_URL}/api/conversations/${conversationId}/messages/stream/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        content,
      }),
    }
  );

  if (!response.ok) {
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
    const { value, done } = await reader.read();

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

  return completedText;
}