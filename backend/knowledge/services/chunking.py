class TextChunkingService:
    """
    Splits document text into smaller chunks for RAG processing.
    """

    def __init__(self, chunk_size: int = 500):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")

        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        """
        Split text into fixed-size chunks.
        """

        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        text = text.strip()

        return [
            text[i : i + self.chunk_size]
            for i in range(0, len(text), self.chunk_size)
        ]