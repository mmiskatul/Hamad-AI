class ConversationRepository:
    async def create_conversation(
        self, user_id: str, title: str, model_id: str
    ) -> dict[str, object]:
        raise NotImplementedError

    async def append_message(
        self, conversation_id: str, role: str, content: str
    ) -> dict[str, object]:
        raise NotImplementedError

    async def list_messages(self, conversation_id: str) -> list[dict[str, object]]:
        raise NotImplementedError
