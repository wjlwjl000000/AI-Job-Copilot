import os
from langchain.agents.middleware import AgentMiddleware


class SkillLoadingMiddleware(AgentMiddleware):
    """按需加载 SKILL .md 文件，填充 system_prompt 占位符 {skills_list} 和 {skill_content}"""

    def __init__(self, skills_dir: str):
        self.skills_dir = skills_dir
        self._skills_meta: dict[str, dict] = {}
        self._loaded_skills: set = set()
        self._load_skills_metadata()

    def _load_skills_metadata(self):
        """启动时仅加载 SKILL name + description"""
        if not os.path.isdir(self.skills_dir):
            return
        for filename in sorted(os.listdir(self.skills_dir)):
            if filename.endswith(".md"):
                filepath = os.path.join(self.skills_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                skill_name = filename.replace(".md", "")
                self._skills_meta[skill_name] = self._parse_frontmatter(content)

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
