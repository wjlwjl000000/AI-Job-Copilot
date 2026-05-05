---
name: match-jobs
description: Use when the user wants to discover job openings matching their profile, needs skill-based career recommendations, or the system proactively suggests new positions after profile changes or application rejections.
---

# Match Jobs

## Overview
Semantic search for job openings using the user's profile vector in Chroma, returning a ranked list with human-readable recommendations.

## When to Use
- User says "帮我搜职位" or "有什么适合我的"
- Profile just built, initial recommendations needed
- After rejection, proactively match new opportunities

## When NOT to Use
- Specific JD needs scoring → `score-match`
- Company research → `web_search` tool

## Workflow
1. **db_read**("user_profiles") → skill context
2. **chroma_query**("jobs", profile_summary, k=10) → semantic search
3. **call_llm**(matches + profile) → rank and generate recommendation reasons

## Output Format
```json
{"matches": [{"job_id": "...", "title": "...", "company": "...", "score": 0.85, "reason": "..."}]}
```

## Common Mistakes
- chroma_query collection set to "profiles" → must be "jobs"
- Returning scores without explanations → call_llm for readable reasons
