from rest_framework.test import APITestCase
from django.urls import reverse
from users.models import User
from unittest.mock import patch

from ai.translation.exceptions import TranslationProviderError

class TranslationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="translation_test",
            email="translation@example.com",
            password="TestPassword123!",
        )
        self.client.force_authenticate(user=self.user)

    def test_translation_success(self):
        url = reverse("translation")

        response = self.client.post(
            url,
            {
                "text": "Hello",
                "source_language": "en",
                "target_language": "fr",
            },
            format="json",
        )    

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["translated_text"],
            "[fr] Hello",
        )

    def test_translation_rejects_empty_text(self):
        url = reverse("translation")

        response = self.client.post(
            url,
            {
                "text": "",
                "source_language": "en",
                "target_language": "fr",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)


    def test_translation_rejects_empty_target_language(self):
        url = reverse("translation")

        response = self.client.post(
            url,
            {
                "text": "Hello",
                "source_language": "en",
                "target_language": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)


    def test_translation_requires_authentication(self):
        self.client.force_authenticate(user=None)

        url = reverse("translation")

        response = self.client.post(
            url,
            {
                "text": "Hello",
                "source_language": "en",
                "target_language": "fr",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)    

    def test_translation_handles_service_error(self):
        url = reverse("translation")

        response = self.client.post(
            url,
            {
                "text": "Hello",
                "source_language": "en",
                "target_language": "fr",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)    

    @patch(
        "conversations.views.AIConversationService.translate_text"
    )
    def test_translation_handles_provider_error(
        self,
        mock_translate,
    ):
        mock_translate.side_effect = TranslationProviderError(
            "Provider failed"
        )

        url = reverse("translation")

        response = self.client.post(
            url,
            {
                "text": "Hello",
                "source_language": "en",
                "target_language": "fr",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            set(response.data.keys()),
            {"error"},
        )
        self.assertEqual(
            set(response.data["error"].keys()),
            {"code", "message"},
        )
        self.assertEqual(
            response.data["error"]["message"],
            "Translation service is currently unavailable.",
        )
        self.assertEqual(
            response.data["error"]["code"],
            "translation_provider_error",
        ) 

    def test_translation_strips_language_whitespace(self):
        url = reverse("translation")

        response = self.client.post(
            url,
            {
                "text": "Hello",
                "source_language": " en ",
                "target_language": " fr ",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["translated_text"],
            "[fr] Hello",
        )   

    def test_translation_response_contract(self):
        url = reverse("translation")

        response = self.client.post(
            url,
            {
                "text": "Hello",
                "source_language": "en",
                "target_language": "fr",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data.keys()),
            {"translated_text"},
        )        