from django.contrib.auth import get_user_model
from django.test import TestCase

from ai.context.conversation import ConversationContextBuilder
from conversations.models import Conversation, Message


class ConversationContextBuilderTests(TestCase):

    def test_build_returns_conversation_messages_in_chronological_order(self):
        user = get_user_model().objects.create_user(
            username="conversationcontext",
            email="conversationcontext@example.com",
            password="testpass123",
        )

        conversation = Conversation.objects.create(
            user=user,
            title="Test Conversation",
        )

        Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_USER,
            content="First message",
        )

        Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_ASSISTANT,
            content="Second message",
        )

        builder = ConversationContextBuilder(
            message_limit=20,
        )

        context = builder.build(conversation)

        self.assertEqual(
            context,
            [
                {
                    "role": "user",
                    "content": "First message",
                },
                {
                    "role": "assistant",
                    "content": "Second message",
                },
            ],
        )

    def test_build_respects_message_limit(self):
        user = get_user_model().objects.create_user(
            username="conversationlimit",
            email="conversationlimit@example.com",
            password="testpass123",
        )

        conversation = Conversation.objects.create(
            user=user,
            title="Limited Conversation",
        )

        for index in range(3):
            Message.objects.create(
                conversation=conversation,
                sender_type=Message.SENDER_USER,
                content=f"Message {index + 1}",
            )

        builder = ConversationContextBuilder(
            message_limit=2,
        )

        context = builder.build(conversation)

        self.assertEqual(
            context,
            [
                {
                    "role": "user",
                    "content": "Message 2",
                },
                {
                    "role": "user",
                    "content": "Message 3",
                },
            ],
        )

    def test_build_excludes_requested_message(self):
        user = get_user_model().objects.create_user(
            username="conversationexclude",
            email="conversationexclude@example.com",
            password="testpass123",
        )

        conversation = Conversation.objects.create(
            user=user,
            title="Exclude Conversation",
        )

        first_message = Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_USER,
            content="First message",
        )

        Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_ASSISTANT,
            content="Second message",
        )

        builder = ConversationContextBuilder()

        context = builder.build(
            conversation,
            exclude_message_id=first_message.id,
        )

        self.assertEqual(
            context,
            [
                {
                    "role": "assistant",
                    "content": "Second message",
                },
            ],
        )

    def test_build_rejects_non_conversation(self):
        builder = ConversationContextBuilder()

        with self.assertRaises(TypeError):
            builder.build("not a conversation")

    def test_build_rejects_negative_message_limit(self):
        with self.assertRaises(ValueError):
            ConversationContextBuilder(
                message_limit=-1,
            )