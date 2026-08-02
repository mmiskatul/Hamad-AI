from pydantic import Field

from app.schemas.common import ApiModel


class AgentRunRequest(ApiModel):
    agent_id: str
    input: str = Field(min_length=1)


class AgentRunResponse(ApiModel):
    run_id: str
    agent_id: str
    status: str
    output: str
