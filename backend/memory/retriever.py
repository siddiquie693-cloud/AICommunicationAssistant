from django.db.models import Q
from django.utils import timezone

from ai.memory.types import MemoryQuery, MemoryResult

from .models import Memory


class DjangoMemoryRetriever:
    """
    Retrieves active, non-expired memories from Django storage.
    """

    def retrieve(self, query: MemoryQuery) -> list[MemoryResult]:
        if not isinstance(query, MemoryQuery):
            raise TypeError("query must be a MemoryQuery.")

        if query.limit < 1:
            return []

        now = timezone.now()

        memories = (
            Memory.objects.filter(
                user_id=query.user_id,
                is_active=True,
            )
            .filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=now)
            )
            .order_by("-importance", "-created_at", "-id")[: query.limit]
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