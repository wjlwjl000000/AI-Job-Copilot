---
name: score-match
description: Use when evaluating how well a resume matches a specific job posting across multiple dimensions (skill overlap, experience, education, salary), or when the user asks "do I fit this role".
---

# Score Match

## Overview
Multi-dimensional evaluation of resume-JD fit. See `references/scoring-dimensions.md` for the detailed rubric.

## When to Use
- User says "我和这个岗位匹配吗" or "这个适合我吗"
- System auto-evaluation before application or interview
- Supervisor dispatches `action: "score"` task

## When NOT to Use
- Just need job list → `match-jobs`
- Already know low match, just need optimization → `optimize-resume`

## Workflow
1. **db_read**("user_profiles") + **db_read**("jobs", id) → both sides
2. **call_llm**(profile + jd) → score across 4 dimensions (see references/)
3. Output scores + strengths + gaps + suggestions

## Output Format
```json
{"overall": 0.45, "skill_match": 0.5, "experience_match": 0.4, "education_match": 0.8, "strengths": [...], "gaps": [...], "suggestions": [...]}
```

## Triggers
- overall < 0.6 → `optimize-resume`
- overall < 0.6 → **call_support_agent**(trigger="low_match")

## Common Mistakes
- Only comparing skill tags, ignoring experience depth
- Forgetting to trigger support agent on low scores
