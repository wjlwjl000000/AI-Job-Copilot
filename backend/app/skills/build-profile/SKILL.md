---
name: build-profile
description: Use when parsed resume data is ready and needs conversion into a structured user profile with skill taxonomy, work experience vector, and competitiveness scores for downstream matching and support agents.
---

# Build Profile

## Overview
Build a structured user profile from parsed resume data with skill grading, vector embedding, and competitiveness scoring. The profile feeds all downstream agents.

## When to Use
- `parse-resume` returned structured data
- User says "更新画像" or "生成我的求职档案"
- Profile data is stale and needs refresh

## When NOT to Use
- Resume not parsed yet → `parse-resume`
- Just need job search → `match-jobs`

## Workflow
1. **db_read**("user_profiles") → existing profile (may be empty)
2. **call_llm**(parsed_data) → grade skills by level, compute work years, generate profile summary
3. **db_write**("user_profiles", data) → persist
4. **chroma_insert**("profiles", [summary]) → vectorize for RAG
5. **call_llm**(profile) → score: competitiveness, market_match, completeness (see `references/skill-taxonomy.md`)

## Output Format
```json
{"profile_id": "...", "skill_tags": [{"name": "Python", "level": "高级"}], "work_years": 3, "scores": {"competitiveness": 0.8, "market_match": 0.6, "completeness": 0.9}}
```

## Common Mistakes
- Skipping chroma_insert → Support agent RAG breaks
- All skills graded as "中级" → use taxonomy in references/
