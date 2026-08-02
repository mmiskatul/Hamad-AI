class DocumentRepository:
    async def save_document(self, source_id: str, text: str) -> dict[str, object]:
        raise NotImplementedError

    async def search(self, query: str, top_k: int) -> list[dict[str, object]]:
        raise NotImplementedError
