import os


def build_skills_list(base_dir: str, names: list[str]) -> str:
    """从 SKILL.md frontmatter 提取 name + description，生成 Agent 提示词中的技能列表。"""
    lines = []
    for name in names:
        path = os.path.join(base_dir, name, "SKILL.md")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                parts = f.read().split("---")
            for line in parts[1].strip().split("\n") if len(parts) >= 3 else []:
                if line.startswith("description:"):
                    lines.append(f"- skill_name: {name}\ndescription: {line.split(':', 1)[1].strip()}\n" + "-" * 10)
                    break
    return "\n".join(lines)
