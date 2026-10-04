from django.db.models import (
    Case,
    ExpressionWrapper,
    IntegerField,
    Q,
    Value,
    When,
)
from django.utils import timezone

from ai.memory.types import MemoryQuery, MemoryResult

from .models import Memory


class DjangoMemoryRetriever:
    """
    Retrieves active, non-expired memories from Django storage
    using deterministic content relevance.
    """

    def retrieve(self, query: MemoryQuery) -> list[MemoryResult]:
        if not isinstance(query, MemoryQuery):
            raise TypeError("query must be a MemoryQuery.")

        if query.limit < 1:
            return []

        if not query.text.strip():
            return []

        now = timezone.now()
        query_terms = query.text.strip().split()

        if not query_terms:
            return []

        content_query = Q()

        for term in query_terms:
            content_query |= Q(content__icontains=term)

        match_score = ExpressionWrapper(
            sum(
                Case(
                    When(
                        content__icontains=term,
                        then=Value(1),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                )
                for term in query_terms
            ),
            output_field=IntegerField(),
        )

        memories = (
            Memory.objects.filter(
                user_id=query.user_id,
                is_active=True,
            )
            .filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=now)
            )
            .filter(content_query)
            .annotate(match_score=match_score)
            .order_by(
                "-match_score",
                "-importance",
                "-created_at",
                "-id",
            )[: query.limit]
        )

        return [
            MemoryResult(
                content=memory.content,
                metadata={
                    "memory_id": memory.id,
                    "memory_type": memory.memory_type,
                    "importance": memory.importance,
                    **memory.metadata,
                },
            )
            for memory in memories
        ]