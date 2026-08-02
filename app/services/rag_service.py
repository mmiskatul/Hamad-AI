class RagService:
    async def ingest(self, source_id: str, content: str) -> None:
        raise NotImplementedError("Wire chunking and embedding here.")

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, object]]:
        raise NotImplementedError("Wire vector retrieval here.")
