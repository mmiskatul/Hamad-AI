class AgentService:
    async def run(self, agent_id: str, input_text: str) -> dict[str, object]:
        raise NotImplementedError("Wire tool-using agent orchestration here.")
