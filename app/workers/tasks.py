"""Background worker task definitions.

Hook Celery / Redis / RQ / Arq into this module once the queue backend is chosen.
"""


async def process_file_upload(file_id: str) -> None:
    raise NotImplementedError("Wire file processing worker here.")


async def build_embeddings(document_id: str) -> None:
    raise NotImplementedError("Wire embedding worker here.")


async def transcribe_audio(job_id: str) -> None:
    raise NotImplementedError("Wire voice transcription worker here.")
