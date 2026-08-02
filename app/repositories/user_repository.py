class UserRepository:
    async def find_by_id(self, user_id: str) -> dict[str, object] | None:
        raise NotImplementedError

    async def find_by_email(self, email: str) -> dict[str, object] | None:
        raise NotImplementedError
