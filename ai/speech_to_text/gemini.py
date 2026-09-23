from decouple import config
from google import genai
import logging

from ai.speech_to_text.base import SpeechToTextProvider
from ai.speech_to_text.exceptions import SpeechToTextProviderError

logger = logging.getLogger(__name__)

class GeminiSpeechToTextProvider(SpeechToTextProvider):
    """
    Speech-to-text provider implementation using Google Gemini.
    """

    def __init__(self):
        self.api_key = config(
            "GEMINI_API_KEY",
            default="",
        )

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.model = config(
            "GEMINI_MODEL",
            default="gemini-3.6-flash",
        )

        self.client = genai.Client(
            api_key=self.api_key,
        )

    def transcribe(
        self,
        audio,
        *,
        language: str | None = None,
    ) -> str:
        if audio is None:
            raise ValueError(
                "Audio cannot be empty."
            )

        import os
        import tempfile

        temporary_path = None

        try:
            suffix = ".m4a"

            original_name = getattr(
                audio,
                "name",
                "",
            )

            if original_name:
                _, extension = os.path.splitext(
                    original_name
                )

                if extension:
                    suffix = extension

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
            ) as temporary_file:
                for chunk in audio.chunks():
                    temporary_file.write(chunk)

                temporary_path = temporary_file.name
            uploaded_file = self.client.files.upload(
                file=temporary_path,
            )               

            prompt = (
                "Transcribe the spoken audio exactly. "
                "Return only the transcription text."
            )

            if language:
                prompt += (
                    f" The spoken language is expected to be "
                    f"{language}."
                )
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    uploaded_file,
                ],
            )   

            return response.text or ""
        except Exception as exc:
            logger.exception("Gemini STT transcription failed.")
            
            raise SpeechToTextProviderError(
                "Failed to transcribe audio using Gemini."
            ) from exc
        finally:
            if temporary_path and os.path.exists(
                temporary_path
            ):
                os.remove(temporary_path)