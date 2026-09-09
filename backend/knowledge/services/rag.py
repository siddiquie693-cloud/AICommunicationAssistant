from knowledge.services.context import RAGContextBuilder
from knowledge.services.retrieval import KnowledgeRetrievalService

class RAGService:
    """
    Orchestrates knowledge retrieval and context construction.
    """

    def __init__(
        self,
        retrieval_service: KnowledgeRetrievalService,
        context_builder: RAGContextBuilder,
    ):
        self.retrieval_service = retrieval_service
        self.context_builder = context_builder

    def build_context(
        self,
        query: str,
        *,
        top_k: int = 5,
    ) -> str:
        """
        Retrieve relevant knowledge and build RAG context.
        """

        results = self.retrieval_service.retrieve(
            query,
            top_k=top_k,
        )

        return self.context_builder.build(results)