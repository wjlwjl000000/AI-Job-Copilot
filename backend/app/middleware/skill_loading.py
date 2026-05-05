import os
from langchain.agents.middleware import AgentMiddleware


class SkillLoadingMiddleware(AgentMiddleware):
    """按需加载 SKILL.md，填充 system_prompt 占位符 {skills_list} 和 {skill_content}"""

    def __init__(self, skills_base_dir: str, skill_names: list[str]):
        self.skills_base_dir = skills_base_dir
        self.skill_names = skill_names
        self._skills_meta: dict[str, dict] = {}
        self._loaded_skills: set = set()
        self._load_skills_metadata()

    def _load_skills_metadata(self):
        """启动时仅加载指定 SKILL 的 name + description"""
        for name in self.skill_names:
            filepath = os.path.join(self.skills_base_dir, name, "SKILL.md")
            if os.path.isfile(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                self._skills_meta[name] = self._parse_frontmatter(content)

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

    def _inject_skill(self, skill_name: str) -> str:
        if skill_name not in self._skills_meta:
            return ""
        self._loaded_skills.add(skill_name)
        return self._skills_meta[skill_name].get("body", "")

    def unload_skill(self, skill_name: str):
        self._loaded_skills.discard(skill_name)

    def get_skills_list_text(self) -> str:
        lines = []
        for name, meta in self._skills_meta.items():
            lines.append(f"- **{name}**: {meta.get('description', '')}")
        return "\n".join(lines) if lines else "无"
