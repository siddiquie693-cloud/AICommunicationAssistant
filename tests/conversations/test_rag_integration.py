from unittest.mock import MagicMock, patch

from django.test import TestCase
from unittest.mock import Mock
from knowledge.services.rag import RAGService
from knowledge.services.embeddings.mock import MockEmbeddingService
from knowledge.services.vector_store.mock import MockVectorStore

from conversations.models import Conversation, Message
from conversations.services.ai_conversation_service import (
    AIConversationService,
)
from users.models import User


class RAGIntegrationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="raguser",
            email="rag@example.com",
            password="TestPassword123",
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            title="RAG Test",
        )

        self.user_message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="What is Python?",
        )

    @patch(
        "conversations.services.ai_conversation_service.get_ai_provider"
    )
    def test_generate_response_works_without_rag(
        self,
        mock_get_provider,
    ):
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider

        service = AIConversationService()

        service.ai_service.generate_response = MagicMock(
            return_value="Python is a programming language."
        )

        response = service.generate_response(
            self.conversation,
            self.user_message,
        )

        self.assertEqual(
            response.content,
            "Python is a programming language.",
        )

        self.assertEqual(
            response.sender_type,
            Message.SENDER_ASSISTANT,
        )

    @patch(
        "conversations.services.ai_conversation_service.get_ai_provider"
    )
    def test_generate_response_with_rag_context(
        self,
        mock_get_provider,
    ):
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider

        service = AIConversationService()

        service.ai_service.generate_response = MagicMock(
            return_value="Python is a programming language."
        )

        rag_context = (
            "Python is a high-level programming language."
        )

        response = service.generate_response(
            self.conversation,
            self.user_message,
            rag_context=rag_context,
        )

        self.assertEqual(
            response.content,
            "Python is a programming language.",
        )

        self.assertEqual(
            response.sender_type,
            Message.SENDER_ASSISTANT,
        )

        service.ai_service.generate_response.assert_called_once()  

        call_args = (
            service.ai_service.generate_response.call_args
        )  

        prompt = call_args.args[0]

        self.assertIn(
            rag_context,
            prompt,
        )

        self.assertIn(
            self.user_message.content,
            prompt,
        )

    @patch(
        "conversations.services.ai_conversation_service.get_ai_provider"
    )
    def test_generate_response_with_empty_rag_context(
        self,
        mock_get_provider,
    ):
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider

        service = AIConversationService()

        service.ai_service.generate_response = MagicMock(
            return_value="Python is a programming language."
        )

        response = service.generate_response(
            self.conversation,
            self.user_message,
            rag_context="",
        )

        self.assertEqual(
            response.content,
            "Python is a programming language.",
        )

        service.ai_service.generate_response.assert_called_once()

        call_args = (
            service.ai_service.generate_response.call_args
        )

        prompt = call_args.args[0]

        self.assertEqual(
            prompt,
            self.user_message.content,
        )  

    @patch(
        "conversations.services.ai_conversation_service.get_ai_provider"
    )
    def test_generate_response_builds_rag_context(
        self,
        mock_get_provider,
    ):
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider

        service = AIConversationService()

        service.ai_service.generate_response = MagicMock(
            return_value="Python is a programming language."
        )

        mock_rag_service = MagicMock()
        mock_rag_service.build_context.return_value = (
            "Python is a high-level programming language."
        )

        service.rag_service = mock_rag_service

        response = service.generate_response(
            self.conversation,
            self.user_message,
        )

        self.assertEqual(
            response.content,
            "Python is a programming language.",
        )

        mock_rag_service.build_context.assert_called_once_with(
            self.user_message.content,
            top_k=5,
        ) 

    @patch(
        "conversations.services.ai_conversation_service.get_ai_provider"
    )
    @patch(
        "conversations.services.ai_conversation_service.RAGService"
    )
    def test_generate_response_uses_rag_service_automatically(
        self,
        mock_rag_service_class,
        mock_get_provider,
    ):
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider

        mock_rag_service = MagicMock()
        mock_rag_service.build_context.return_value = (
            "Python is a high-level programming language."
        )
        mock_rag_service_class.return_value = mock_rag_service

        service = AIConversationService()

        service.ai_service.generate_response = MagicMock(
            return_value="Python is a programming language."
        )

        response = service.generate_response(
            self.conversation,
            self.user_message,
        )

        self.assertEqual(
            response.content,
            "Python is a programming language.",
        )

        mock_rag_service.build_context.assert_called_once_with(
            self.user_message.content,
            top_k=5,
        )

        prompt = (
            service.ai_service.generate_response
            .call_args.args[0]
        )

        self.assertIn(
            "Python is a high-level programming language.",
            prompt,
        )  

    @patch(
        "conversations.services.ai_conversation_service.get_ai_provider"
    )
    @patch(
        "conversations.services.ai_conversation_service.RAGService"
    )
    def test_generate_response_passes_top_k_to_rag_service(
        self,
        mock_rag_service_class,
        mock_get_provider,
    ):
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider

        mock_rag_service = MagicMock()
        mock_rag_service.build_context.return_value = (
            "Python knowledge context."
        )
        mock_rag_service_class.return_value = mock_rag_service

        service = AIConversationService()

        service.ai_service.generate_response = MagicMock(
            return_value="Python is a programming language."
        )

        response = service.generate_response(
            self.conversation,
            self.user_message,
            rag_top_k=3,
        )

        self.assertEqual(
            response.content,
            "Python is a programming language.",
        )

        mock_rag_service.build_context.assert_called_once_with(
            self.user_message.content,
            top_k=3,
        )      

    @patch(
        "conversations.services.ai_conversation_service.get_ai_provider"
    )
    def test_generate_response_rejects_invalid_rag_top_k(
        self,
        mock_get_provider,
    ):
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider

        service = AIConversationService()

        with self.assertRaises(ValueError):
            service.generate_response(
                self.conversation,
                self.user_message,
                rag_top_k=0,
            )

    @patch(
        "conversations.services.ai_conversation_service.get_ai_provider"
    )
    def test_generate_response_rejects_negative_rag_top_k(
        self,
        mock_get_provider,
    ):
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider

        service = AIConversationService()

        with self.assertRaises(ValueError):
            service.generate_response(
                self.conversation,
                self.user_message,
                rag_top_k=-1,
            )  

    @patch(
        "conversations.services.ai_conversation_service.get_ai_provider"
    )
    @patch(
        "conversations.services.ai_conversation_service.RAGService"
    )
    def test_generate_response_uses_default_rag_top_k(
        self,
        mock_rag_service_class,
        mock_get_provider,
    ):
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider

        mock_rag_service = MagicMock()
        mock_rag_service.build_context.return_value = (
            "Python knowledge context."
        )
        mock_rag_service_class.return_value = mock_rag_service

        service = AIConversationService()

        service.ai_service.generate_response = MagicMock(
            return_value="Python is a programming language."
        )

        response = service.generate_response(
            self.conversation,
            self.user_message,
        )

        self.assertEqual(
            response.content,
            "Python is a programming language.",
        )

        mock_rag_service.build_context.assert_called_once_with(
            self.user_message.content,
            top_k=5,
        )              

    def test_generate_response_accepts_injected_rag_service(self):
        rag_service = Mock()
        rag_service.build_context.return_value = "Injected knowledge"

        service = AIConversationService(
            provider_name="mock",
            rag_service=rag_service,
        )

        self.assertIs(service.rag_service, rag_service)    

    def test_default_rag_service_is_created(self):
        service = AIConversationService(
            provider_name="mock",
        )

        self.assertIsNotNone(service.rag_service)
        self.assertIsInstance(service.rag_service, RAGService)  

    def test_default_rag_service_uses_injected_dependencies(self):
        embedding_service = MockEmbeddingService()
        vector_store = MockVectorStore()

        service = AIConversationService(
            provider_name="mock",
            embedding_service=embedding_service,
            vector_store=vector_store,
        )      

        self.assertIs(
            service.rag_service.retrieval_service.embedding_service,
            embedding_service,
        )

        self.assertIs(
            service.rag_service.retrieval_service.vector_store,
            vector_store,
        )

    def test_rag_top_k_can_be_configured(self):
        rag_service = Mock()
        rag_service.build_context.return_value = ""

        service = AIConversationService(
            provider_name="mock",
            rag_service=rag_service,
        )    

        conversation = Conversation.objects.create(
            user=self.user,
            title="Test Conversation",
        )

        user_message = Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_USER,
            content="what is RAG?",
        )

        service.generate_response(
            conversation,
            user_message,
            rag_top_k=10,
        )

        rag_service.build_context.assert_called_once_with(
            "what is RAG?",
            top_k=10,
        )

    def test_generate_response_works_without_rag_context(self):
        rag_service = Mock()
        rag_service.build_context.return_value = ""

        service = AIConversationService(
            provider_name="mock",
            rag_service=rag_service,
        )

        conversation = Conversation.objects.create(
            user=self.user,
            title="No Knowledge",
        )

        user_message = Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_USER,
            content="Hello",
        )

        response = service.generate_response(
            conversation,
            user_message,
        )

        self.assertIsNotNone(response)
        self.assertEqual(
            response.sender_type,
            Message.SENDER_ASSISTANT,
        )

        rag_service.build_context.assert_called_once_with(
            "Hello",
            top_k=5,
        )    

     