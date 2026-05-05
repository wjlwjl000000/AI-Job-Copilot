---
name: optimize-resume
description: Use when a resume needs tailoring for a specific JD, after score-match shows gaps (below 0.6), or when the user explicitly requests resume rewording for a target role.
---

# Optimize Resume

## Overview
Generate an optimized resume version for a target JD. Creates a new version without overwriting the original. See `references/optimization-guidelines.md` for do's and don'ts.

## When to Use
- `score-match` returns overall < 0.6
- User says "帮我优化简历" or "针对这个岗位改一下"
- User dissatisfied with match score

## When NOT to Use
- No score-match done → score first to identify gaps
- Just need match analysis → `score-match`

## Workflow
1. **db_read**("resumes") → base version
2. **db_read**("jobs", id) → JD + identified gaps
3. **call_llm**(resume + jd + gaps) → optimized version:
   - Highlight matching skills and experience
   - Rephrase to align with JD keywords
   - Never fabricate experience (see references/)
4. **db_write**("resumes", optimized) → new version (base_version=false)

## Output Format
```json
{"optimized_resume_id": "...", "changes": [{"original": "...", "optimized": "...", "reason": "..."}], "improvements": [...]}
```

## Common Mistakes
- Overwriting the base version → always create new
- Fabricating experience to match JD → only rephrase phrasing
