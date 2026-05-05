---
name: generate-interview-qs
description: Use when the user has an upcoming interview and needs targeted preparation questions based on the JD requirements and their profile weaknesses, or when the system detects an application in interview stage.
---

# Generate Interview Questions

## Overview
Generate 3-5 targeted interview questions covering the user's weak areas and the JD's core requirements. See `references/question-types.md` for question taxonomy and examples.

## When to Use
- User says "帮我准备面试" or "面试会问什么"
- Application status enters "interview" stage
- Score-match reveals clear knowledge gaps

## When NOT to Use
- User has answered questions, needs evaluation → `evaluate-answer`
- Just need general interview tips → call_llm directly

## Workflow
1. **db_read**("user_profiles") + **db_read**("jobs", id) → weaknesses + JD
2. **call_llm**(profile + jd + weaknesses) → generate 3-5 questions:
   - Mix of question types (behavioral, technical, system design)
   - Each with focus area and answer tips
3. Need more job details → return `state: "input-required"`

## Output Format
```json
{"questions": [{"question": "...", "type": "technical", "focus": "...", "tips": "..."}]}
```

## Common Mistakes
- Generic questions ignoring user weaknesses → must target gaps
- Questions without tips → each needs focus + suggested points
