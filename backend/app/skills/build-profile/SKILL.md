---
name: build-profile
description: Use when parsed resume text or skill descriptions are available and need conversion into a structured job-seeker profile for downstream matching, scoring, or interview preparation agents. Also use when an existing profile needs updating with new skills, target roles, or preferences.
---

# Build Profile

## Overview
Convert resume text and user preferences into a structured `UserProfile` persisted in PostgreSQL and vectorized in Chroma for downstream agents.

## When to Use
- `parse-resume` returned structured data or user provided skill descriptions
- User says "生成我的求职画像", "更新画像", or "分析我的技能"
- Profile data is stale or target role changed

## When NOT to Use
- Resume file not yet parsed → `parse-resume`
- Just need job search → `match-jobs`
- Just need match score → `score-match`

## Workflow
1. **先检查是否已有画像** — db_read("user_profiles") 查询用户是否已有画像记录，如果有则需要基于最新输入进行更新而非覆盖
2. **构建并持久化画像** — db_write("user_profiles", data) 将完整的结构化画像写入数据库：
   - 从用户输入的简历文本或技能描述中提取信息
   - 按 references/skill-taxonomy.md 的标准将技能分级
   - 计算工作年限、整理教育背景和项目经验
   - 综合评估竞争力、市场匹配度和画像完整度
3. **生成向量便于检索** — chroma_insert("profiles", [summary], [metadata]) 用画像摘要（技能+目标岗位+年限的简洁描述）创建向量，使下游 Matching Agent 和 Support Agent 能通过语义搜索找到该画像

> 步骤2中的技能分级、年限计算、摘要生成和竞争力评分均在Agent的Thought阶段自然完成，不需要call_llm工具。

## Output Format
```
{
  "profile_id": "数据库生成的画像ID",
  "skill_tags": [{"name": "技能名", "level": "初级|中级|高级|专家"}],
  "work_years": "工作年限（整数）",
  "education": {"degree": "学历", "school": "学校", "major": "专业"},
  "projects": [{"name": "项目名", "description": "描述", "tech_stack": ["技术栈"]}],
  "target": {"cities": ["期望城市"], "salary_range": "期望薪资范围", "industry": "目标行业", "roles": ["目标岗位"]},
  "scores": {"competitiveness": "0-1竞争力分", "market_match": "0-1市场匹配分", "completeness": "0-1画像完整度分"}
}
```

## Common Mistakes
- Skipping chroma_insert → downstream matching/support agents break
- All skills graded as "中级" → use taxonomy in `references/skill-taxonomy.md`
- Omitting scores field → required by downstream agents
- db_read returned an existing profile but directly overwritten without merging → check before writing
