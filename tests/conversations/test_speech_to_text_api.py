from io import BytesIO

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ai.speech_to_text.exceptions import SpeechToTextProviderError
from users.models import User


class SpeechToTextAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="sttuser",
            email="stt@example.com",
            password="TestPassword123!",
        )
        self.client.force_authenticate(user=self.user)

    def test_speech_to_text_api(self):
        url = reverse("speech-to-text")

        audio = BytesIO(b"fake-audio-data")
        audio.name = "test.wav"

        response = self.client.post(
            url,
            {
                "audio": audio,
                "language": "en",
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["transcribed_text"],
            "Mock transcription",
        )

    def test_speech_to_text_api_provider_error(self):
        url = reverse("speech-to-text")

        class FailingSpeechToTextService:
            def transcribe(self, audio, *, language=None):
                raise SpeechToTextProviderError(
                    "STT provider failed"
                )    

        from conversations.services.ai_conversation_service import (
            AIConversationService,
        )    

        service = AIConversationService(
            speech_to_text_service=FailingSpeechToTextService(),
        )

        from unittest.mock import patch

        with patch(
            "conversations.views.AIConversationService",
            return_value=service,
        ):
            audio = BytesIO(b"fake-audio-data")
            audio.name = "test.wav"

            response = self.client.post(
                url,
                {
                    "audio": audio,
                    "language": "en",
                },
                format="multipart",
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )    

        self.assertEqual(
            response.data["error"]["code"],
            "speech_to_text_provider_error",
        )

        self.assertEqual(
            response.data["error"]["message"],
            "Speech-to-text service is currently unavailable.",
        )

    def test_speech_to_text_api_missing_audio(self):
        url = reverse("speech-to-text")

        response = self.client.post(
            url,
            {
                "language": "en",
            },
            fromat="multipart",
        )    

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_speech_to_text_api_empty_audio(self):
        url = reverse("speech-to-text")

        audio = BytesIO(b"")
        audio.name = "empty.wav"

        response = self.client.post(
            url,
            {
                "audio": audio,
                "language": "en",
            },
            format="multipart",
        )    

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_speech_to_text_api_empty_language(self):
        url = reverse("speech-to-text")

        audio = BytesIO(b"fake-audio-data")
        audio.name = "test.wav"

        response = self.client.post(
            url,
            {
                "audio": audio,
                "language": "",
            },
            format="multipart",
        )    

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )