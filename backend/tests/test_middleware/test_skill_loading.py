import pytest
import os
import tempfile
from app.middleware.skill_loading import SkillLoadingMiddleware


def test_parse_frontmatter_extracts_name_and_description():
    middleware = SkillLoadingMiddleware(skills_base_dir="/fake", skill_names=[])
    content = "---\nname: test-skill\ndescription: 用于测试的场景\n---\n# Title\n工作流程：\n1. 步骤一"
    result = middleware._parse_frontmatter(content)
    assert result["name"] == "test-skill"
    assert result["description"] == "用于测试的场景"
    assert "工作流程" in result["body"]


def test_load_skills_metadata_from_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create flat structure: tmpdir/test-skill/SKILL.md
        skill_dir = os.path.join(tmpdir, "test-skill")
        os.makedirs(skill_dir)
        skill_path = os.path.join(skill_dir, "SKILL.md")
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write("---\nname: test-skill\ndescription: 测试用\n---\n# Body\ncontent here")
        middleware = SkillLoadingMiddleware(skills_base_dir=tmpdir, skill_names=["test-skill"])
        assert "test-skill" in middleware._skills_meta
        assert middleware._skills_meta["test-skill"]["name"] == "test-skill"


def test_inject_skill_returns_body():
    middleware = SkillLoadingMiddleware(skills_base_dir="/fake", skill_names=[])
    middleware._skills_meta = {"test-skill": {"name": "test", "description": "desc", "body": "# Skill Body\ncontent"}}
    body = middleware._inject_skill("test-skill")
    assert "# Skill Body" in body
    assert "test-skill" in middleware._loaded_skills
