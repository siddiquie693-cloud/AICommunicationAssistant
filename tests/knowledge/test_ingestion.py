from django.test import TestCase

from knowledge.models import KnowledgeDocument
from knowledge.services.ingestion import DocumentIngestionService
from users.models import User

class DocumentIngestionServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="ingestionuser",
            email="ingestion@example.com",
            password="TestPassword123",
        )
        self.service = DocumentIngestionService()

    def test_ingest_returns_clean_content(self):
        document = KnowledgeDocument.objects.create(
            user=self.user,
            title="Python",
            content="  Python is powerful.  ",
        )    

        result = self.service.ingest(document)

        self.assertEqual(result, "Python is powerful.")

    def test_ingest_rejects_empty_content(self):
        document = KnowledgeDocument.objects.create(
            user=self.user,
            title="Empty",
            content="  ",
        )    

        with self.assertRaises(ValueError):
            self.service.ingest(document)