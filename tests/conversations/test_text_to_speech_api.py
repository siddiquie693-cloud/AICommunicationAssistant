from io import BytesIO

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from ai.text_to_speech.exceptions import TextToSpeechProviderError


User = get_user_model()


class TextToSpeechAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="ttsuser",
            email="tts@example.com",
            password="TestPassword123!",
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_text_to_speech_api(self):
        url = reverse("text-to-speech")

        response = self.client.post(
            url,
            {
                "text": "Hello world",
                "language": "en",
                "voice": "default",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["audio"],
            b"Mock audio data",
        )

    def test_text_to_speech_api_provider_error(self):
        url = reverse("text-to-speech")

        class FailingTextToSpeechService:
            def synthesize(
                self,
                text,
                *,
                language=None,
                voice=None,
            ):
                raise TextToSpeechProviderError(
                    "TTS provider failed"
                )

        from conversations.services.ai_conversation_service import (
            AIConversationService,
        )

        service = AIConversationService(
            text_to_speech_service=FailingTextToSpeechService(),
        )

        from unittest.mock import patch

        with patch(
            "conversations.views.AIConversationService",
            return_value=service,
        ):
            response = self.client.post(
                url,
                {
                    "text": "Hello world",
                    "language": "en",
                    "voice": "default",
                },
                format="json",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

        self.assertEqual(
            response.data["error"]["code"],
            "text_to_speech_provider_error",
        )

        self.assertEqual(
            response.data["error"]["message"],
            "Text-to-speech service is currently unavailable.",
        )

    def test_text_to_speech_api_missing_text(self):
        url = reverse("text-to-speech")

        response = self.client.post(
            url,
            {
                "language": "en",
                "voice": "default",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


    def test_text_to_speech_api_empty_text(self):
        url = reverse("text-to-speech")

        response = self.client.post(
            url,
            {
                "text": "",
                "language": "en",
                "voice": "default",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


    def test_text_to_speech_api_empty_language(self):
        url = reverse("text-to-speech")

        response = self.client.post(
            url,
            {
                "text": "Hello world",
                "language": "",
                "voice": "default",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )    

    def test_text_to_speech_api_empty_voice(self):
        url = reverse("text-to-speech")

        response = self.client.post(
            url,
            {
                "text": "Hello world",
                "language": "en",
                "voice": "",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )    

    def test_text_to_speech_api_requires_authentication(self):
        self.client.force_authenticate(user=None)

        url = reverse("text-to-speech")

        response = self.client.post(
            url,
            {
                "text": "Hello world",
                "language": "en",
                "voice": "default",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )    
            