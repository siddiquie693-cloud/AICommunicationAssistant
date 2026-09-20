import { API_BASE_URL } from './config';
import { File, Paths } from 'expo-file-system';

export async function transcribeAudio(
  token,
  audioUri,
  language
) {
  if (!token) {
    throw new Error('Authentication token is required.');
  }

  if (!audioUri) {
    throw new Error('Recorded audio is required.');
  }

  const audioFile = new File(audioUri);

  if (!audioFile.exists) {
    throw new Error(
      'Recorded audio file does not exist.'
    );
  }

  const formData = new FormData();

  formData.append(
    'audio',
    audioFile
  );

  if (language) {
    formData.append(
      'language',
      language
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/api/conversations/speech-to-text/`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    }
  );

  if (!response.ok) {
    let errorMessage =
      'Speech-to-text request failed.';

    try {
      const data = await response.json();

      errorMessage =
        data?.error?.message ||
        data?.detail ||
        errorMessage;
    } catch (error) {
      // Keep the default error message.
    }

    throw new Error(errorMessage);
  }

  const data = await response.json();

  if (!data?.transcribed_text) {
    throw new Error(
      'Speech-to-text returned an empty transcription.'
    );
  }

  return data.transcribed_text;
}

export async function synthesizeSpeech(
  token,
  text,
  language,
  voice
) {
  if (!token) {
    throw new Error(
      'Authentication token is required.'
    );
  }

  if (!text || !text.trim()) {
    throw new Error(
      'Text is required for speech synthesis.'
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/api/conversations/text-to-speech/`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text.trim(),
        ...(language ? { language } : {}),
        ...(voice ? { voice } : {}),
      }),
    }
  );

  if (!response.ok) {
    let errorMessage =
      'Text-to-speech request failed.';

    try {
      const data = await response.json();

      errorMessage =
        data?.error?.message ||
        data?.detail ||
        errorMessage;
    } catch (error) {
      // Keep the default error message.
    }

    throw new Error(errorMessage);
  }

  const audioData =
    await response.arrayBuffer();

  if (!audioData.byteLength) {
    throw new Error(
      'Text-to-speech returned empty audio.'
    );
  }

  const fileName =
    `tts-${Date.now()}.wav`;

  const audioFile =
    new File(
      Paths.cache,
      fileName
    );

  audioFile.write(
    new Uint8Array(audioData)
  );

  return audioFile.uri;
}