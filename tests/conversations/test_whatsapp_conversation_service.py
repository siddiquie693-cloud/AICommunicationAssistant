from unittest.mock import Mock

from django.test import TestCase
from django.contrib.auth import get_user_model

from conversations.models import Conversation, Message
from conversations.services.whatsapp_conversation_service import (
    WhatsAppConversationService,
)


class WhatsAppConversationServiceTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="whatsapp_test_user",
            email="whatsapp@test.com",
            password="TestPassword123!",
        )
    
        self.whatsapp_service = Mock()
        self.ai_conversation_service = Mock()

        self.service = WhatsAppConversationService(
            self.whatsapp_service,
            self.ai_conversation_service,
        )

    def test_get_user_by_whatsapp_number_returns_user(self):
        self.user.whatsapp_phone_number = "919876543210"
        self.user.save(update_fields=["whatsapp_phone_number"])

        result = self.service.get_user_by_whatsapp_number(
            "919876543210"
        )

        self.assertEqual(result, self.user)

    def test_get_user_by_whatsapp_number_rejects_unknown_number(self):
        with self.assertRaisesMessage(
            ValueError,
            "No user found for the WhatsApp phone number.",
        ):
            self.service.get_user_by_whatsapp_number(
                "919999999999"
            )  

    def test_get_user_by_whatsapp_number_rejects_empty_number(self):
        with self.assertRaisesMessage(
            ValueError,
            "WhatsApp phone number cannot be empty.",
        ):
            self.service.get_user_by_whatsapp_number("   ")          

    def test_get_or_create_conversation_creates_conversation(self):
        conversation = self.service.get_or_create_conversation(
            self.user,
        )

        self.assertIsInstance(
            conversation,
            Conversation,
        )
        self.assertEqual(
            conversation.user,
            self.user,
        )
        self.assertEqual(
            conversation.title,
            "WhatsApp Conversation",
        )

    def test_get_or_create_conversation_returns_existing_conversation(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="Existing Conversation",
        )

        result = self.service.get_or_create_conversation(
            self.user,
            conversation_id=conversation.id,
        )

        self.assertEqual(
            result,
            conversation,
        )

    def test_process_message_creates_user_message(self):
        assistant_message = Mock()
        assistant_message.content = "AI response"

        self.ai_conversation_service.generate_response.return_value = (
            assistant_message
        )

        result = self.service.process_message(
            self.user,
            "919999999999",
            "  Hello AI  ",
        )

        self.assertEqual(
            result["user_message"].content,
            "Hello AI",
        )
        self.assertEqual(
            result["user_message"].sender_type,
            Message.SENDER_USER,
        )

    def test_process_message_generates_assistant_response(self):
        assistant_message = Mock()
        assistant_message.content = "AI response"

        self.ai_conversation_service.generate_response.return_value = (
            assistant_message
        )

        result = self.service.process_message(
            self.user,
            "919999999999",
            "Hello AI",
        )

        self.ai_conversation_service.generate_response.assert_called_once_with(
            result["conversation"],
            result["user_message"],
            target_language=None,
        )

    def test_process_message_sends_assistant_response_to_whatsapp(self):
        assistant_message = Mock()
        assistant_message.content = "AI response"

        self.ai_conversation_service.generate_response.return_value = (
            assistant_message
        )

        self.service.process_message(
            self.user,
            "919999999999",
            "Hello AI",
        )

        self.whatsapp_service.send_message.assert_called_once_with(
            "919999999999",
            "AI response",
        )

    def test_get_or_create_conversation_rejects_other_users_conversation(self):
        User = get_user_model()

        other_user = User.objects.create_user(
            username="other_whatsapp_user",
            email="other-whatsapp@test.com",
            password="TestPassword123!",
        )

        conversation = Conversation.objects.create(
            user=other_user,
            title="Other User Conversation",
        )

        with self.assertRaises(Conversation.DoesNotExist):
            self.service.get_or_create_conversation(
                self.user,
                conversation_id=conversation.id,
            )

    def test_process_message_passes_target_language_to_ai_service(self):
        assistant_message = Mock()
        assistant_message.content = "Hola"

        self.ai_conversation_service.generate_response.return_value = (
            assistant_message
        )

        result = self.service.process_message(
            self.user,
            "919999999999",
            "Hello",
            target_language="es",
        )

        self.ai_conversation_service.generate_response.assert_called_once_with(
            result["conversation"],
            result["user_message"],
            target_language="es",
        )    

    def test_process_message_rejects_empty_message(self):
        with self.assertRaisesMessage(
            ValueError,
            "Message cannot be empty.",
        ):
            self.service.process_message(
                self.user,
                "919999999999",
                "   ",
            )