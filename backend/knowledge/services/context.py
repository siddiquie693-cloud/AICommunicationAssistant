class RAGContextBuilder:
    """
    Builds a context string from retrieved knowledge.
    """

    def build(
        self,
        results: list[tuple[str, float]],
    ) -> str:
        """
        Combine retrieved knowledge into a single context block.
        """

        if not results:
            return ""

        return "\n\n".join(
            content.strip()
            for content, _score in results
            if content and content.strip()
        )