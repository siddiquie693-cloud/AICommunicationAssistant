from django.test import TestCase

from users.models import User
from knowledge.models import KnowledgeDocument

class KnowledgeDocumentModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
        )

    def test_create_knowledge_document(self):
        document = KnowledgeDocument.objects.create(
            user=self.user,
            title="Python Basics",
            content="Python is a programming language.",
        )    

        self.assertEqual(document.user, self.user)
        self.assertEqual(document.title, "Python Basics")
        self.assertEqual(
            document.content,
            "Python is a programming language.",
        )

    def test_string_representation(self):
        document = KnowledgeDocument.objects.create(
            user=self.user,
            title="Django Guide",
            content="Django is a Python web framework.",
        )    

        self.assertEqual(str(document), "Django Guide")

    def test_document_belong_to_user(self):
        document = KnowledgeDocument.objects.create(
            user=self.user,
            title="My Document",
            content="Private knowledge.",
        )    

        self.assertEqual(
            self.user.knowledge_documents.count(),
            1,
        )

        self.assertEqual(
            self.user.knowledge_documents.first(),
            document,
        )

    def test_timestamps_are_created(self):
        document = KnowledgeDocument.objects.create(
            user=self.user,
            title="Timestamp Test",
            content="Testing timestamps.",
        )    

        self.assertIsNotNone(document.created_at)
        self.assertIsNotNone(document.updated_at)