from pydantic import BaseModel


class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    examples: list[str] = []


class AgentCard(BaseModel):
    a2a_version: str = "1.0"
    id: str
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: dict = {"streaming": True, "pushNotifications": False}
    skills: list[AgentSkill] = []
    defaultInputModes: list[str] = ["text", "application/json"]
    defaultOutputModes: list[str] = ["text", "application/json"]


def create_agent_card(agent_id: str, name: str, description: str, url: str, skills: list[dict]) -> AgentCard:
    return AgentCard(
        id=agent_id,
        name=name,
        description=description,
        url=url,
        skills=[AgentSkill(**s) for s in skills],
    )
