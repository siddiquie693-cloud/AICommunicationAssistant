import io
import os
import wave

from google import genai
from google.genai import types

from ai.text_to_speech.base import TextToSpeechProvider
from ai.text_to_speech.exceptions import TextToSpeechProviderError


class GeminiTextToSpeechProvider(TextToSpeechProvider):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-3.1-flash-tts-preview",
    ):
        self.api_key = (
            api_key
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )

        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY or GEMINI_API_KEY is required."
            )

        self.client = genai.Client(
            api_key=self.api_key
        )
        self.model = model

    def synthesize(
        self,
        text: str,
        *,
        language: str | None = None,
        voice: str | None = None,
    ) -> bytes:
        if not text or not text.strip():
            raise ValueError(
                "Text cannot be empty."
            )

        try:
            voice_name = voice or "Kore"

            prompt = text.strip()

            if language:
                prompt = (
                    f"Speak the following text in "
                    f"{language}:\n\n"
                    f"{prompt}"
                )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=(
                                types.PrebuiltVoiceConfig(
                                    voice_name=voice_name,
                                )
                            )
                        )
                    ),
                ),
            )

            audio_data = (
                response
                .candidates[0]
                .content
                .parts[0]
                .inline_data
                .data
            )

            if not audio_data:
                raise ValueError(
                    "Gemini returned empty audio data."
                )

            return self._pcm_to_wav(audio_data)

        except Exception as exc:
            print(
                "GEMINI TTS ERROR:",
                repr(exc),
            )

            raise TextToSpeechProviderError(
                "Failed to synthesize speech using Gemini."
            ) from exc

    @staticmethod
    def _pcm_to_wav(
        pcm_data: bytes,
        channels: int = 1,
        sample_rate: int = 24000,
        sample_width: int = 2,
    ) -> bytes:
        buffer = io.BytesIO()

        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)

        return buffer.getvalue()