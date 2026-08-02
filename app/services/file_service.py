class FileService:
    async def ingest(self, filename: str, raw_bytes: bytes) -> dict[str, object]:
        raise NotImplementedError("Wire extraction, OCR, and chunk storage here.")
