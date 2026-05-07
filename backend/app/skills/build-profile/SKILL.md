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
   - 如果用户提供了目标 JD 文本，提取并结构化存入 jd 字段：{content: "JD原文", requirements: [{skill, level, required}]}
   - 综合评估竞争力、市场匹配度和画像完整度
3. **生成向量便于检索** — chroma_insert("profiles", [summary], [metadata]) 用画像摘要（技能+目标岗位+年限的简洁描述）创建向量，使下游 Matching Agent 和 Support Agent 能通过语义搜索找到该画像

> 步骤2中的技能分级、年限计算、摘要生成、JD解析和竞争力评分均在Agent的Thought阶段自然完成，不需要call_llm工具。

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

## Data Models

### user_profiles（读/写）
| 字段 | 类型 | 含义 |
|------|------|------|
| id | UUID | 画像唯一ID |
| user_id | UUID | 所属用户ID |
| skill_tags | JSON | 技能标签列表：[{name, level: "初级|中级|高级|专家"}] |
| work_years | INT | 工作年限 |
| education | JSON | 学历信息：{degree, school, major} |
| projects | JSON | 项目经验：[{name, description, tech_stack}] |
| target | JSON | 求职目标：{cities, salary_range, industry, roles} |
| preference | JSON | 用户偏好设置 |
| jd | JSON | 目标JD：{content: "JD原文", requirements: [{skill, level, required}]} |
| scores | JSON | 竞争力评分：{competitiveness, market_match, completeness} 均为0-1 |

## Examples

### 示例1：首次上传简历构建画像
**场景**：用户上传了一份简历文件，尚未有画像记录。

**工具调用序列**：
1. db_read("user_profiles") → []（确认无已有画像）

2. db_write("user_profiles", {
     "user_id": "u-default",
     "skill_tags": [
       {"name": "Python", "level": "高级"},
       {"name": "FastAPI", "level": "中级"},
       {"name": "PostgreSQL", "level": "中级"},
       {"name": "Docker", "level": "初级"}
     ],
     "work_years": 4,
     "education": {"degree": "本科", "school": "XX大学", "major": "计算机科学"},
     "projects": [
       {"name": "智能客服系统", "description": "基于LangChain的RAG客服机器人", "tech_stack": ["Python", "LangChain", "FAISS"]}
     ],
     "target": {"cities": ["北京", "杭州"], "salary_range": "25k-35k", "industry": "AI应用", "roles": ["AI工程师", "后端开发"]},
     "scores": {"competitiveness": 0.72, "market_match": 0.65, "completeness": 0.80}
   })
   → {"id": "prof-abc123"}

3. chroma_insert("profiles", ["4年Python后端开发，目标AI工程师/后端开发，技能：Python(高级) FastAPI(中级) PostgreSQL(中级) Docker(初级)"], [{"profile_id": "prof-abc123"}])
   → {"ids": ["vec-001"]}

**最终输出**：
{
  "profile_id": "prof-abc123",
  "skill_tags": [{"name": "Python", "level": "高级"}, ...],
  "work_years": 4,
  "scores": {"competitiveness": 0.72, "market_match": 0.65, "completeness": 0.80}
}

### 示例2：已有画像时基于新输入更新
**场景**：用户之前构建过画像，说"我又学了Rust，目标换成后端开发"。

**工具调用序列**：
1. db_read("user_profiles") → [{"id": "prof-abc123", "skill_tags": [...], "target": {...}, ...}]（已有画像，需基于新输入更新）

2. db_write("user_profiles", {
     "id": "prof-abc123",
     "skill_tags": [...原有技能..., {"name": "Rust", "level": "初级"}],
     "target": {...原有target..., "roles": ["后端开发"]},
     "scores": {"competitiveness": 0.75, "market_match": 0.68, "completeness": 0.85}
   })
   → {"id": "prof-abc123"}

3. chroma_insert("profiles", ["更新摘要..."], [{"profile_id": "prof-abc123"}])

**最终输出**：合并后的完整画像（新增Rust技能，目标岗位已更新）

> 示例中的字段值来自db_read返回的实际数据或用户输入。步骤中标注"在Thought中..."的部分由Agent基于已有数据推理，不得凭空构造字段值。
