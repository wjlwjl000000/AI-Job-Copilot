import os
from langchain.agents.middleware import AgentMiddleware


class SkillLoadingMiddleware(AgentMiddleware):
    """通过 before_model 钩子注入 SKILL 内容到 system prompt。"""

    def __init__(self, skills_base_dir: str, skill_names: list[str]):
        super().__init__()
        self._skills: dict[str, dict] = {}
        for name in skill_names:
            path = os.path.join(skills_base_dir, name, "SKILL.md")
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                meta = self._parse_frontmatter(content)
                self._skills[name] = {
                    "name": name,
                    "description": meta.get("description", ""),
                    "body": meta.get("body", ""),
                }

    def _parse_frontmatter(self, content: str) -> dict:
        parts = content.split("---")
        if len(parts) < 3:
            return {"name": "unknown", "description": "", "body": content}
        frontmatter = {}
        for line in parts[1].strip().split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                frontmatter[key.strip()] = val.strip()
        frontmatter["body"] = parts[2].strip()
        return frontmatter

    def before_model(self, state, runtime):
        skills_list = "\n".join([
            f"- **{n}**: {m['description']}" for n, m in self._skills.items()
        ])
        skill_content = state.get("skill_content", "")

        msgs = state.get("messages", [])
        for msg in msgs:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                msg.content = msg.content.replace("{skills_list}", skills_list)
                msg.content = msg.content.replace("{skill_content}", skill_content)
        return None
