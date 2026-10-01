class RAGContextBuilder:
    """
    Builds a context string from retrieved knowledge
    and optional personal profile context.
    """

    def build(
        self,
        results: list[tuple[str, float]],
        profile_context: str | None = None,
    ) -> str:
        """
        Combine retrieved knowledge and optional personal profile
        context into a single context block.
        """

        context_parts = []

        if profile_context and profile_context.strip():
            context_parts.append(
                profile_context.strip()
            )

        if results:
            context_parts.extend(
                content.strip()
                for content, _score in results
                if content and content.strip()
            )

        return "\n\n".join(context_parts)