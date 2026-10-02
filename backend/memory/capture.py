from .services import MemoryService


class MemoryCaptureService:
    """
    Creates persistent memories from explicitly identified memory candidates.
    """

    @staticmethod
    def capture(
        *,
        user,
        content,
        memory_type,
        importance=3,
        expires_at=None,
        metadata=None,
    ):
        if not isinstance(content, str) or not content.strip():
            return None

        return MemoryService.create_memory(
            user=user,
            content=content.strip(),
            memory_type=memory_type,
            importance=importance,
            expires_at=expires_at,
            metadata=metadata,
        )

    @staticmethod
    def capture_explicit_memory(
        *,
        user,
        content,
        memory_type,
        importance=3,
        expires_at=None,
        metadata=None,
    ):
        """
        Creates a persistent memory only when the caller has
        explicitly identified the content as a memory.
        """
        return MemoryCaptureService.capture(
            user=user,
            content=content,
            memory_type=memory_type,
            importance=importance,
            expires_at=expires_at,
            metadata={
                **(metadata or {}),
                "capture_mode": "explicit",
            },
        )