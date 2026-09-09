from knowledge.models import KnowledgeDocument


class DocumentIngestionService:
    """
    Handles ingestion of knowledge documents.
    """

    def ingest(self, document: KnowledgeDocument) -> str:
        """
        Prepare a document's content for downstream RAG processing.
        """

        if not document.content or not document.content.strip():
            raise ValueError("Document content cannot be empty.")

        return document.content.strip()