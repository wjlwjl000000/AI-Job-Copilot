from app.a2a.client import A2AClient


class AgentRegistry:
    SYSTEM_AGENTS = {"profile-agent", "matching-agent", "interview-agent", "support-agent"}

    def __init__(self, client: A2AClient = None):
        self.client = client or A2AClient()
        self._agents: dict[str, dict] = {}

    async def discover(self, agent_urls: list[str]):
        for url in agent_urls:
            try:
                card = await self.client.fetch_agent_card(url)
                card["_url"] = url
                self._agents[card["name"]] = card
            except Exception:
                pass

    async def register(self, agent_url: str) -> dict:
        card = await self.client.fetch_agent_card(agent_url)
        card["_url"] = agent_url
        self._agents[card["name"]] = card
        return card

    def get_agent_url(self, name: str) -> str | None:
        agent = self._agents.get(name)
        return agent["_url"] if agent else None

    def get_all_summaries(self) -> list[dict]:
        return [
            {
                "name": name,
                "description": card["description"],
                "skills": card.get("skills", []),
                "inputSchema": card.get("inputSchema", {"fields": []}),
            }
            for name, card in self._agents.items()
            if "support" not in name.lower()
        ]

    def is_system_agent(self, name: str) -> bool:
        return name in self.SYSTEM_AGENTS

    def list_all(self) -> list[dict]:
        return [{"name": name, "card": card} for name, card in self._agents.items()]

    def unregister(self, name: str):
        if name in self._agents:
            del self._agents[name]
